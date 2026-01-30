import sqlite3
import os
import random
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from helpers.city_normalizer import normalize_city_name, smart_city_to_english

# Create logger for database operations
db_logger = logging.getLogger('database')

class Database:
    def __init__(self, db_path: str = "drink_bot.db"):
        self.db_path = db_path
        self.geolocator = Nominatim(user_agent="drink_bot")
        self.recreate_db_if_needed()
        self.init_db()
    
    def _log_query(self, query: str, params: tuple = None, user_id: int = None, step: str = None):
        """Log database query with details"""
        try:
            # Create log record with extra fields
            record = logging.LogRecord(
                name='database',
                level=logging.DEBUG,
                pathname='',
                lineno=0,
                msg=f"SQL QUERY: {query}",
                args=(),
                exc_info=None
            )
            
            if params:
                record.query = f"{query} | PARAMS: {params}"
            else:
                record.query = query
                
            if user_id:
                record.user_id = user_id
                
            if step:
                record.step = step
                
            db_logger.handle(record)
            
        except Exception as e:
            logging.error(f"Error logging query: {e}")
    
    def normalize_city(self, city_text: str) -> str:
        """Normalize city name using unified function"""
        return normalize_city_name(city_text)
    
    def recreate_db_if_needed(self):
        """Check if all required columns exist, recreate DB if needed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if profiles table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='profiles'
                """)
                table_exists = cursor.fetchone()
                
                if not table_exists:
                    # Table doesn't exist, will be created by init_db
                    print("Profiles table doesn't exist, will be created")
                    return
                
                # Check if all required columns exist
                cursor.execute("PRAGMA table_info(profiles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                required_columns = ['language', 'is_premium', 'lat', 'lon', 'who_pays', 'city_display', 'city_normalized']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    logging.warning(f"Missing columns detected: {missing_columns}")
                    logging.info("Recreating database with correct structure...")
                    
                    # Close connection and delete database file
                    conn.close()
                    
                    # Delete old database file
                    if os.path.exists(self.db_path):
                        os.remove(self.db_path)
                        logging.info(f"Deleted old database file: {self.db_path}")
                    
                    logging.info("Database will be recreated with correct structure")
                    
        except Exception as e:
            logging.error(f"Error checking database structure: {e}")
            # If there's any error, try to recreate
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logging.warning(f"Deleted corrupted database file: {self.db_path}")
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create profiles table with all required columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL DEFAULT('other') CHECK(gender IN ('male', 'female', 'other')),
                    city TEXT NOT NULL,
                    city_display TEXT,
                    city_normalized TEXT,
                    favorite_drink TEXT NOT NULL,
                    photo_id TEXT,
                    who_pays TEXT NOT NULL DEFAULT('each_self') CHECK(who_pays IN ('each_self', 'i_treat', 'someone_treats')),
                    language TEXT NOT NULL DEFAULT('ru') CHECK(language IN ('ru', 'ua', 'en')),
                    lat REAL,
                    lon REAL,
                    is_premium INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check and add missing columns for existing tables
            self._migrate_profile_table(cursor)
            self._migrate_events_table(cursor)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(from_user_id, to_user_id),
                    FOREIGN KEY (from_user_id) REFERENCES profiles (user_id),
                    FOREIGN KEY (to_user_id) REFERENCES profiles (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    place TEXT NOT NULL,
                    price_type TEXT NOT NULL CHECK(price_type IN ('free', 'paid')),
                    description TEXT NOT NULL,
                    city TEXT NOT NULL,
                    city_normalized TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL DEFAULT('active') CHECK(status IN ('active', 'expired', 'cancelled')),
                    FOREIGN KEY (creator_id) REFERENCES profiles (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS event_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(event_id, user_id),
                    FOREIGN KEY (event_id) REFERENCES events (id),
                    FOREIGN KEY (user_id) REFERENCES profiles (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER NOT NULL,
                    user2_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user1_id, user2_id),
                    FOREIGN KEY (user1_id) REFERENCES profiles (user_id),
                    FOREIGN KEY (user2_id) REFERENCES profiles (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    interests TEXT NOT NULL,
                    meeting_place TEXT NOT NULL,
                    max_members INTEGER NOT NULL DEFAULT 10,
                    city TEXT NOT NULL,
                    city_normalized TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT('active') CHECK(status IN ('active', 'full', 'cancelled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES profiles (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, user_id),
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (user_id) REFERENCES profiles (user_id)
                )
            ''')
            conn.commit()
    
    def _migrate_profile_table(self, cursor):
        """Migrate existing profiles table to add missing columns"""
        try:
            # Get current table schema
            cursor.execute("PRAGMA table_info(profiles)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'username' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN username TEXT')
                logging.info("Added 'username' column to profiles table")
            
            # Add missing columns
            if 'language' not in columns:
                cursor.execute('''
                    ALTER TABLE profiles 
                    ADD COLUMN language TEXT NOT NULL DEFAULT('ru') CHECK(language IN ('ru', 'ua', 'en'))
                ''')
                logging.info("Added 'language' column to profiles table")
            
            if 'who_pays' not in columns:
                cursor.execute('''
                    ALTER TABLE profiles 
                    ADD COLUMN who_pays TEXT NOT NULL DEFAULT('each_self') CHECK(who_pays IN ('each_self', 'i_treat', 'someone_treats'))
                ''')
                logging.info("Added 'who_pays' column to profiles table")
            
            if 'city_display' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN city_display TEXT')
                logging.info("Added 'city_display' column to profiles table")
            
            if 'city_normalized' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN city_normalized TEXT')
                logging.info("Added 'city_normalized' column to profiles table")
            
            if 'lat' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN lat REAL')
                logging.info("Added 'lat' column to profiles table")
            
            if 'lon' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN lon REAL')
                logging.info("Added 'lon' column to profiles table")
            
            if 'is_premium' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN is_premium INTEGER DEFAULT 0')
                logging.info("Added 'is_premium' column to profiles table")
            
            if 'gender' not in columns:
                cursor.execute('''
                    ALTER TABLE profiles 
                    ADD COLUMN gender TEXT NOT NULL DEFAULT('other') CHECK(gender IN ('male', 'female', 'other'))
                ''')
                logging.info("Added 'gender' column to profiles table")
            
            if 'is_bot' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN is_bot INTEGER DEFAULT 0')
                logging.info("Added 'is_bot' column to profiles table")
            
            if 'bot_photo_path' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN bot_photo_path TEXT')
                logging.info("Added 'bot_photo_path' column to profiles table")
            
            if 'last_rotation_date' not in columns:
                cursor.execute('ALTER TABLE profiles ADD COLUMN last_rotation_date TEXT')
                logging.info("Added 'last_rotation_date' column to profiles table")
                
        except sqlite3.Error as e:
            logging.error(f"Migration error: {e}")
    
    def _migrate_events_table(self, cursor):
        """Migrate existing events table to add missing columns"""
        try:
            # Get current table schema
            cursor.execute("PRAGMA table_info(events)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns
            if 'city_normalized' not in columns:
                cursor.execute('ALTER TABLE events ADD COLUMN city_normalized TEXT')
                logging.info("Added 'city_normalized' column to events table")
                
                # Update existing events with normalized city names
                cursor.execute('SELECT id, city FROM events')
                events = cursor.fetchall()
                for event_id, city in events:
                    if city:
                        city_normalized = self.normalize_city(city)
                        cursor.execute('UPDATE events SET city_normalized = ? WHERE id = ?', 
                                     (city_normalized, event_id))
                logging.info(f"Updated {len(events)} existing events with normalized city names")
            
            if 'expires_at' not in columns:
                # Add expires_at column (4 hours from now for existing events)
                cursor.execute('ALTER TABLE events ADD COLUMN expires_at TIMESTAMP')
                logging.info("Added 'expires_at' column to events table")
                
                # Set expires_at for existing events (4 hours from now)
                import datetime
                future_time = datetime.datetime.now() + datetime.timedelta(hours=4)
                cursor.execute('UPDATE events SET expires_at = ?', (future_time,))
                logging.info(f"Set expires_at for existing events to {future_time}")
            
            if 'status' not in columns:
                cursor.execute('ALTER TABLE events ADD COLUMN status TEXT DEFAULT "active"')
                logging.info("Added 'status' column to events table")
                
                # Set default value for existing rows
                cursor.execute('UPDATE events SET status = "active" WHERE status IS NULL')
                
        except sqlite3.Error as e:
            logging.error(f"Events migration error: {e}")
    
    def create_profile(self, user_id: int, name: str, age: int, gender: str, city: str, favorite_drink: str, photo_id: str = None, who_pays: str = 'each_self', language: str = 'ru', username: str = None) -> bool:
        """Create a new user profile with unified city normalization and detailed logging"""
        try:
            # Normalize city name using unified function
            city_normalized = self.normalize_city(city)
            
            # Use smart English translation for display
            city_display = smart_city_to_english(city)
            
            logging.info(f"DEBUG: Создан профиль пользователя {user_id}. Город в базе: '{city_normalized}', отображение: '{city_display}'")
            
            query = '''
                INSERT OR REPLACE INTO profiles (user_id, username, name, age, gender, city, city_display, city_normalized, favorite_drink, photo_id, who_pays, language, is_bot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            '''
            params = (user_id, username, name, age, gender, city_display, city_display, city_normalized, favorite_drink, photo_id, who_pays, language)
            
            # Log the query before execution
            self._log_query(query, params, user_id, "CREATE_PROFILE")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"DEBUG: User {user_id} from city '{city}', saved as '{city_normalized}'")
                else:
                    logging.warning(f"DEBUG: User {user_id} profile creation affected 0 rows")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE для пользователя {user_id}: {e}")
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE: SQL не выполнен - {query}")
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE: Параметры - {params}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE для пользователя {user_id}: Неожиданная ошибка - {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ CREATE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
    
    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except sqlite3.Error as e:
            logging.error(f"DB Error getting profile: {e}")
            return None
    
    def find_profiles_for_swipe(self, user_id: int, city: str = None, gender: str = None, limit: int = 10) -> list:
        """Find profiles for swiping with proper error handling"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get already liked user IDs
                cursor.execute('SELECT to_user_id FROM likes WHERE from_user_id = ?', (user_id,))
                liked_ids = [row[0] for row in cursor.fetchall()]
                logging.info(f"DEBUG: User {user_id} already liked {len(liked_ids)} profiles")
                
                # Exclude own profile and already liked profiles - ensure all are integers
                exclude_ids = [int(user_id)] + [int(liked_id) for liked_id in liked_ids if liked_id is not None]
                placeholders = ','.join(['?' for _ in exclude_ids])
                
                # Ensure limit is integer
                limit = int(limit) if limit else 10
                
                if city and city.strip():
                    # Normalize the search city and search ONLY in city_normalized
                    city_normalized = self.normalize_city(city.strip())
                    logging.info(f"DEBUG: Searching in city_normalized='{city_normalized}' (from input: '{city}')")
                    
                    # Build query safely
                    query = f'''
                        SELECT * FROM profiles 
                        WHERE city_normalized = ? AND user_id NOT IN ({placeholders})
                        ORDER BY created_at DESC 
                        LIMIT ?
                    '''
                    params = [city_normalized] + exclude_ids + [limit]
                    
                    logging.info(f"DEBUG: Query: {query}")
                    logging.info(f"DEBUG: Params: {params}")
                    
                    cursor.execute(query, params)
                else:
                    logging.warning(f"DEBUG: No city provided for user {user_id}, searching all profiles")
                    
                    query = f'''
                        SELECT * FROM profiles 
                        WHERE user_id NOT IN ({placeholders})
                        ORDER BY created_at DESC 
                        LIMIT ?
                    '''.format(placeholders)
                    params = exclude_ids + [limit]
                    
                    logging.info(f"DEBUG: Query: {query}")
                    logging.info(f"DEBUG: Params: {params}")
                    
                    cursor.execute(query, params)
                
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id}")
                for profile in profiles:
                    logging.debug(f"DEBUG: Profile {profile['user_id']}: city_normalized='{profile.get('city_normalized')}'")
                
                return profiles
                
        except Exception as e:
            logging.error(f"DEBUG: Real error in find_profiles_for_swipe: {e}")
            import traceback
            logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
            return []
    
    def get_profile_likes(self, user_id: int) -> list:
        """Get profiles liked by user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    JOIN likes l ON p.user_id = l.to_user_id
                    WHERE l.from_user_id = ?
                    ORDER BY l.created_at DESC
                ''', (user_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
        except sqlite3.Error as e:
            print(f"Error getting profile likes: {e}")
            return []
    
    def like_profile(self, from_user_id: int, to_user_id: int) -> bool:
        """Like a profile"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO likes (from_user_id, to_user_id, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (from_user_id, to_user_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error liking profile: {e}")
            return False
    
    def get_mutual_likes(self, user_id: int) -> list:
        """Get mutual likes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    WHERE p.user_id IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                        INTERSECT
                        SELECT from_user_id FROM likes WHERE to_user_id = ?
                    )
                ''', (user_id, user_id))
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
        except sqlite3.Error as e:
            print(f"Error getting mutual likes: {e}")
            return []
    
    def get_city_bot_count(self, city: str) -> int:
        """Get count of bots in city"""
        try:
            city_normalized = self.normalize_city(city)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM profiles 
                    WHERE is_bot = 1 AND city_normalized = ?
                ''', (city_normalized,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"Error getting city bot count: {e}")
            return 0
    
    def get_daily_limits(self, city: str) -> dict:
        """Get daily limits for city"""
        try:
            city_normalized = self.normalize_city(city)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT daily_limit, bots_shown, date 
                    FROM daily_bot_limits 
                    WHERE city_normalized = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (city_normalized,))
                result = cursor.fetchone()
                if result:
                    return {
                        'daily_limit': result[0],
                        'current_count': result[1],
                        'last_rotation_date': result[2]
                    }
                else:
                    return {'daily_limit': 5, 'current_count': 0, 'last_rotation_date': None}
        except sqlite3.Error as e:
            print(f"Error getting daily limits: {e}")
            return {'daily_limit': 5, 'current_count': 0, 'last_rotation_date': None}
    
    def delete_profile(self, user_id: int) -> bool:
        """Delete user profile"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM profiles WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM likes WHERE from_user_id = ? OR to_user_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM matches WHERE user1_id = ? OR user2_id = ?', (user_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def add_like(self, from_user_id: int, to_user_id: int) -> bool:
        """Add a like from one user to another"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO likes (from_user_id, to_user_id)
                    VALUES (?, ?)
                ''', (from_user_id, to_user_id))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"Like added: {from_user_id} -> {to_user_id}")
                else:
                    logging.warning(f"Like already exists: {from_user_id} -> {to_user_id}")
                return success
        except sqlite3.Error as e:
            logging.error(f"Error adding like: {e}")
            return False
    
    def check_mutual_like(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users have mutual likes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM likes 
                    WHERE (from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?)
                ''', (user1_id, user2_id, user2_id, user1_id))
                result = cursor.fetchone()
                is_mutual = result[0] == 2
                if is_mutual:
                    logging.info(f"Mutual like detected: {user1_id} <-> {user2_id}")
                return is_mutual
        except sqlite3.Error as e:
            logging.error(f"Error checking mutual like: {e}")
            return False
    
    def create_match(self, user1_id: int, user2_id: int) -> bool:
        """Create a match between two users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO matches (user1_id, user2_id)
                    VALUES (?, ?)
                ''', (min(user1_id, user2_id), max(user1_id, user2_id)))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error creating match: {e}")
            return False
    
    def get_user_matches(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all matches for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    JOIN matches m ON (p.user_id = m.user1_id OR p.user_id = m.user2_id)
                    WHERE (m.user1_id = ? OR m.user2_id = ?) AND p.user_id != ?
                ''', (user_id, user_id, user_id))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"Error getting user matches: {e}")
            return []
    
    def get_icebreaker(self) -> str:
        """Get a random icebreaker topic"""
        icebreakers = [
            "Какой ваш любимый бар в городе?",
            "Что лучше: крафт или классика?",
            "Самый необычный коктейль, который вы пробовали?",
            "Ваш идеальный вечер с друзьями?",
            "Какой напиток ассоциируется с вашим настроением сегодня?",
            "Расскажите о самой запоминающейся вечеринке",
            "Какой коктейль вы бы назвали своим именем?",
            "Предпочитаете шумные компании или уютные посиделки?",
            "Какой напиток никогда не попробуете?",
            "Ваш любимый тост за дружбу?"
        ]
        return random.choice(icebreakers)
    
    def create_event(self, creator_id: int, name: str, place: str, price_type: str, description: str, city: str) -> bool:
        """Create a new event with unified city normalization and expiration time"""
        try:
            # Normalize city name using unified function
            city_normalized = self.normalize_city(city)
            logging.info(f"DEBUG: Создано событие '{name}'. Город в базе: '{city_normalized}'")
            
            # Set expiration time (4 hours from now)
            import datetime
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=4)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = '''
                    INSERT INTO events (creator_id, name, place, price_type, description, city, city_normalized, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (creator_id, name, place, price_type, description, city, city_normalized, expires_at)
                
                # Log the query before execution
                self._log_query(query, params, creator_id, "CREATE_EVENT")
                
                cursor.execute(query, params)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"Event created successfully: '{name}' in {city_normalized}, expires at {expires_at}")
                else:
                    logging.warning(f"Event creation affected 0 rows")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT для пользователя {creator_id}: {e}")
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT: SQL не выполнен - {query}")
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT: Параметры - {params}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT: Traceback - {traceback.format_exc()}")
            return False
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT для пользователя {creator_id}: Неожиданная ошибка - {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ CREATE_EVENT: Traceback - {traceback.format_exc()}")
            return False
    
    def get_events_by_city(self, city: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events in a specific city using city_normalized with exact match and expiration filter"""
        try:
            # Normalize the search city using unified function
            city_normalized = self.normalize_city(city)
            logging.info(f"DEBUG: Поиск тусовок в городе: '{city_normalized}'")
            
            import datetime
            now = datetime.datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Exact match query with expiration filter
                query = '''
                    SELECT e.*, p.name as creator_name, COUNT(ep.user_id) as current_members
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    LEFT JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.city_normalized = ? AND e.expires_at > ? AND e.status = 'active'
                    GROUP BY e.id
                    ORDER BY e.created_at DESC
                    LIMIT ?
                '''
                params = (city_normalized, now, limit)
                
                # Log the query before execution
                self._log_query(query, params, None, "GET_EVENTS_BY_CITY")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                events = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Найдено {len(events)} активных тусовок в городе '{city_normalized}'")
                
                # Log each event's expiration time for debugging
                for event in events:
                    time_remaining = self.get_time_remaining(event['expires_at'])
                    logging.debug(f"DEBUG: Event '{event['name']}' expires in {time_remaining}")
                
                return events
                
        except sqlite3.Error as e:
            logging.error(f"Error getting events: {e}")
            return []
    
    def is_user_participating(self, event_id: int, user_id: int) -> bool:
        """Check if user is participating in an event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM event_participants WHERE event_id = ? AND user_id = ?', (event_id, user_id))
                result = cursor.fetchone()
                return result is not None
        except sqlite3.Error as e:
            logging.error(f"Error checking user participation: {e}")
            return False
    
    def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user's language preference in user_settings table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_settings (user_id, language, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, language))
                conn.commit()
                logging.info(f"Language saved to user_settings for user {user_id}: {language}")
                return True
        except sqlite3.Error as e:
            logging.error(f"DB Error updating user language: {e}")
            return False
    
    def update_user_city_normalized(self, user_id: int, city_display: str, city_normalized: str) -> bool:
        """Update user's city_display and city_normalized"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE profiles 
                    SET city_display = ?, city_normalized = ? 
                    WHERE user_id = ?
                ''', (city_display, city_normalized, user_id))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"Updated city for user {user_id}: display='{city_display}', normalized='{city_normalized}'")
                else:
                    logging.warning(f"No profile found to update city for user {user_id}")
                return success
        except sqlite3.Error as e:
            logging.error(f"DB Error updating user city: {e}")
            return False
    
    def get_icebreaker(self) -> str:
        """Get a random icebreaker question"""
        icebreakers = [
            "Какой твой любимый коктейль?",
            "Расскажи о самой смешной ситуации в баре",
            "Если бы мог выбрать любое место для питья, где бы это было?",
            "Какой напиток идеально описывает твой характер?",
            "Самый необычный коктейль, который ты пробовал?",
            "Что предпочитаешь: пиво, вино или коктейли?",
            "Расскажи о лучшей вечеринке в твоей жизни",
            "Если бы мог создать свой коктейль, какие ингредиенты бы добавил?",
            "Какое место для встреч тебе нравится больше всего?",
            "Что для тебя идеальный вечер с друзьями?"
        ]
        import random
        icebreaker = random.choice(icebreakers)
        logging.debug(f"Selected icebreaker: {icebreaker}")
        return icebreaker
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's language preference from user_settings first, then profiles"""
        try:
            # First try user_settings table
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT language FROM user_settings WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                if result:
                    language = result[0]
                    logging.debug(f"Language from user_settings for user {user_id}: {language}")
                    return language
            
            # Fallback to profiles table
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT language FROM profiles WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                language = result[0] if result else 'ru'
                logging.debug(f"Language from profiles for user {user_id}: {language}")
                return language
        except sqlite3.Error as e:
            logging.error(f"DB Error getting user language: {e}")
            return 'ru'

    def get_user_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get events created by a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM events 
                    WHERE creator_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"Error getting user events: {e}")
            return []
    
    def join_event(self, event_id: int, user_id: int) -> bool:
        """Join an event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO event_participants (event_id, user_id)
                    VALUES (?, ?)
                ''', (event_id, user_id))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"User {user_id} joined event {event_id}")
                else:
                    logging.warning(f"User {user_id} already in event {event_id}")
                return success
        except sqlite3.Error as e:
            logging.error(f"Error joining event: {e}")
            return False
    
    def leave_event(self, event_id: int, user_id: int) -> bool:
        """Leave an event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM event_participants 
                    WHERE event_id = ? AND user_id = ?
                ''', (event_id, user_id))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"User {user_id} left event {event_id}")
                else:
                    logging.warning(f"User {user_id} was not in event {event_id}")
                return success
        except sqlite3.Error as e:
            logging.error(f"Error leaving event: {e}")
            return False
    
    def get_event_participants(self, event_id: int) -> List[Dict[str, Any]]:
        """Get all participants of an event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    JOIN event_participants ep ON p.user_id = ep.user_id
                    WHERE ep.event_id = ?
                    ORDER BY ep.joined_at
                ''', (event_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"Error getting event participants: {e}")
            return []
    
    def is_user_in_event(self, event_id: int, user_id: int) -> bool:
        """Check if user is already in event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM event_participants 
                    WHERE event_id = ? AND user_id = ?
                ''', (event_id, user_id))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Error checking event participation: {e}")
            return False
    
    def get_events_with_participation(self, city: str, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events in city with user participation status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT e.*, p.name as creator_name,
                           CASE WHEN ep.user_id IS NOT NULL THEN 1 ELSE 0 END as is_participant
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    LEFT JOIN event_participants ep ON e.id = ep.event_id AND ep.user_id = ?
                    WHERE e.city = ?
                    ORDER BY e.created_at DESC
                    LIMIT ?
                ''', (user_id, city, limit))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"Error getting events with participation: {e}")
            return []
    
    def create_company(self, creator_id: int, name: str, description: str, interests: str, meeting_place: str, max_members: int, city: str) -> bool:
        """Create a new company"""
        try:
            city_normalized = self.normalize_city(city)
            logging.info(f"DEBUG: Создана компания '{name}'. Город в базе: '{city_normalized}'")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO companies (creator_id, name, description, interests, meeting_place, max_members, city, city_normalized)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (creator_id, name, description, interests, meeting_place, max_members, city, city_normalized))
                company_id = cursor.lastrowid

                # Ensure creator is a member of their own company
                cursor.execute('''
                    INSERT OR IGNORE INTO company_members (company_id, user_id)
                    VALUES (?, ?)
                ''', (company_id, creator_id))

                conn.commit()
                logging.info(f"Company created successfully: '{name}' in {city_normalized} (id={company_id})")
                return True
        except sqlite3.Error as e:
            logging.error(f"Error creating company: {e}")
            return False

    def get_user_companies(self, user_id: int) -> List[Dict[str, Any]]:
        """Get companies where user is a member (including creator)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = '''
                    SELECT c.*, p.name as creator_name, COUNT(cm2.user_id) as current_members
                    FROM companies c
                    JOIN profiles p ON c.creator_id = p.user_id
                    JOIN company_members cm ON c.id = cm.company_id AND cm.user_id = ?
                    LEFT JOIN company_members cm2 ON c.id = cm2.company_id
                    WHERE c.status IN ('active', 'full')
                    GROUP BY c.id
                    ORDER BY c.created_at DESC
                '''
                params = (user_id,)

                cursor.execute(query, params)
                results = cursor.fetchall()
                companies = [dict(row) for row in results]
                logging.info(f"DEBUG: Found {len(companies)} user companies for user {user_id}")
                return companies
        except sqlite3.Error as e:
            logging.error(f"Error getting user companies: {e}")
            return []
    
    def get_companies_by_city(self, city: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get companies in a specific city using city_normalized with exact match"""
        try:
            city_normalized = self.normalize_city(city)
            logging.info(f"DEBUG: Поиск компаний в городе: '{city_normalized}'")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT c.*, p.name as creator_name, COUNT(cm.user_id) as current_members
                    FROM companies c
                    JOIN profiles p ON c.creator_id = p.user_id
                    LEFT JOIN company_members cm ON c.id = cm.company_id
                    WHERE c.city_normalized = ? AND c.status = 'active'
                    GROUP BY c.id
                    ORDER BY c.created_at DESC
                    LIMIT ?
                ''', (city_normalized, limit))
                
                results = cursor.fetchall()
                companies = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Найдено {len(companies)} компаний в городе '{city_normalized}'")
                return companies
                
        except sqlite3.Error as e:
            logging.error(f"Error getting companies: {e}")
            return []
    
    def join_company(self, company_id: int, user_id: int) -> bool:
        """Join a company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if company is not full
                cursor.execute('SELECT max_members FROM companies WHERE id = ? AND status = "active"', (company_id,))
                company = cursor.fetchone()
                if not company:
                    return False
                
                max_members = company[0]
                
                # Check current members
                cursor.execute('SELECT COUNT(*) FROM company_members WHERE company_id = ?', (company_id,))
                current_members = cursor.fetchone()[0]
                
                if current_members >= max_members:
                    logging.warning(f"Company {company_id} is full")
                    return False
                
                # Add member
                cursor.execute('''
                    INSERT OR IGNORE INTO company_members (company_id, user_id)
                    VALUES (?, ?)
                ''', (company_id, user_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"User {user_id} joined company {company_id}")
                    
                    # Check if company is now full
                    if current_members + 1 >= max_members:
                        cursor.execute('UPDATE companies SET status = "full" WHERE id = ?', (company_id,))
                        conn.commit()
                        logging.info(f"Company {company_id} is now full")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"Error joining company: {e}")
            return False
    
    def leave_company(self, company_id: int, user_id: int) -> bool:
        """Leave a company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM company_members 
                    WHERE company_id = ? AND user_id = ?
                ''', (company_id, user_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"User {user_id} left company {company_id}")
                    
                    # Update company status back to active if it was full
                    cursor.execute('UPDATE companies SET status = "active" WHERE id = ? AND status = "full"', (company_id,))
                    conn.commit()
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"Error leaving company: {e}")
            return False
    
    def is_user_in_company(self, company_id: int, user_id: int) -> bool:
        """Check if user is in a company"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM company_members WHERE company_id = ? AND user_id = ?', (company_id, user_id))
                result = cursor.fetchone()
                return result is not None
        except sqlite3.Error as e:
            logging.error(f"Error checking company membership: {e}")
            return False
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get event by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT e.*, p.name as creator_name, p.username as creator_username
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    WHERE e.id = ?
                '''
                params = (event_id,)
                
                # Log the query before execution
                self._log_query(query, params, None, "GET_EVENT_BY_ID")
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except sqlite3.Error as e:
            logging.error(f"Error getting event by ID: {e}")
            return None

    def get_user_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get events created by user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT e.*, p.name as creator_name, COUNT(ep.user_id) as current_members
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    LEFT JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.creator_id = ?
                    GROUP BY e.id
                    ORDER BY e.created_at DESC
                '''
                params = (user_id,)
                
                # Log the query before execution
                self._log_query(query, params, user_id, "GET_USER_EVENTS")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                events = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(events)} events for user {user_id}")
                return events
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ GET_USER_EVENTS для пользователя {user_id}: {e}")
            return []

    def get_time_remaining(self, expires_at: str) -> str:
        """Calculate time remaining until expiration"""
        try:
            import datetime
            now = datetime.datetime.now()
            
            # Parse expires_at from string
            if isinstance(expires_at, str):
                expires_dt = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            else:
                expires_dt = expires_at
            
            delta = expires_dt - now
            
            if delta.total_seconds() <= 0:
                return "00:00"
            
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            
            return f"{hours:02d}:{minutes:02d}"
            
        except Exception as e:
            logging.error(f"Error calculating time remaining: {e}")
            return "??:??"
    
    def update_profile(self, user_id: int, name: str = None, age: int = None, city: str = None, favorite_drink: str = None, photo_id: str = None, who_pays: str = None, language: str = None, username: str = None, is_premium: int = None) -> bool:
        """Update user profile with detailed logging"""
        try:
            # Get current profile first
            current = self.get_profile(user_id)
            if not current:
                logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: Profile not found for user {user_id}")
                return False
            
            # Build update query dynamically
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if age is not None:
                updates.append("age = ?")
                params.append(age)
            
            if city is not None:
                city_normalized = self.normalize_city(city)
                updates.append("city = ?")
                params.append(city)
                updates.append("city_display = ?")
                params.append(city)
                updates.append("city_normalized = ?")
                params.append(city_normalized)
            
            if favorite_drink is not None:
                updates.append("favorite_drink = ?")
                params.append(favorite_drink)
            
            if photo_id is not None:
                updates.append("photo_id = ?")
                params.append(photo_id)
            
            if who_pays is not None:
                updates.append("who_pays = ?")
                params.append(who_pays)
            
            if language is not None:
                updates.append("language = ?")
                params.append(language)

            if username is not None:
                updates.append("username = ?")
                params.append(username)

            if is_premium is not None:
                updates.append("is_premium = ?")
                params.append(int(is_premium))
            
            if not updates:
                logging.warning(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: No fields to update for user {user_id}")
                return False
            
            # Add user_id to params
            params.append(user_id)
            
            query = f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = ?"
            
            # Log the query before execution
            self._log_query(query, tuple(params), user_id, "UPDATE_PROFILE")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"DEBUG: Profile updated for user {user_id}")
                else:
                    logging.warning(f"DEBUG: Profile update affected 0 rows for user {user_id}")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE для пользователя {user_id}: {e}")
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: SQL не выполнен - {query}")
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: Параметры - {tuple(params)}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE для пользователя {user_id}: Неожиданная ошибка - {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ UPDATE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
    
    def get_user_events(self, user_id: int) -> List[Dict[str, Any]]:
        """Get events created by user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT e.*, p.name as creator_name, COUNT(ep.user_id) as current_members
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    LEFT JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.creator_id = ?
                    GROUP BY e.id
                    ORDER BY e.created_at DESC
                '''
                params = (user_id,)
                
                # Log the query before execution
                self._log_query(query, params, user_id, "GET_USER_EVENTS")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                events = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(events)} events for user {user_id}")
                return events
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ GET_USER_EVENTS для пользователя {user_id}: {e}")
            return []
    
    def delete_event(self, event_id: int, creator_id: int) -> bool:
        """Delete event if user is creator"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = '''
                    DELETE FROM events 
                    WHERE id = ? AND creator_id = ?
                '''
                params = (event_id, creator_id)
                
                # Log the query before execution
                self._log_query(query, params, creator_id, "DELETE_EVENT")
                
                cursor.execute(query, params)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"DEBUG: Event {event_id} deleted by user {creator_id}")
                else:
                    logging.warning(f"DEBUG: Event {event_id} deletion affected 0 rows")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT для пользователя {creator_id}: {e}")
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT: SQL не выполнен - {query}")
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT: Параметры - {params}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT: Traceback - {traceback.format_exc()}")
            return False
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT для пользователя {creator_id}: Неожиданная ошибка - {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ DELETE_EVENT: Traceback - {traceback.format_exc()}")
            return False
    
    def get_company_members_with_usernames(self, company_id: int) -> List[Dict[str, Any]]:
        """Get company members with usernames and names"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT p.user_id, p.name, p.username, cm.joined_at
                    FROM company_members cm
                    JOIN profiles p ON cm.user_id = p.user_id
                    WHERE cm.company_id = ?
                    ORDER BY cm.joined_at ASC
                '''
                params = (company_id,)
                
                # Log the query before execution
                self._log_query(query, params, None, "GET_COMPANY_MEMBERS")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                members = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(members)} members for company {company_id}")
                return members
                
        except sqlite3.Error as e:
            logging.error(f"Error getting company members: {e}")
            return []

    def get_profiles_for_swiping_nearby(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get profiles for swiping including nearby cities"""
        try:
            # Get user profile and city
            user_profile = self.get_profile(user_id)
            if not user_profile:
                return []
            
            user_city_normalized = user_profile.get('city_normalized', '')
            if not user_city_normalized:
                return []
            
            # Define nearby cities mapping (simplified version)
            nearby_cities = {
                'Kyiv': ['Kharkiv', 'Odesa', 'Lviv', 'Dnipro'],
                'Kharkiv': ['Kyiv', 'Poltava', 'Sumy'],
                'Odesa': ['Kyiv', 'Mykolaiv', 'Kherson'],
                'Lviv': ['Kyiv', 'Ivano-Frankivsk', 'Ternopil'],
                'Dnipro': ['Kyiv', 'Zaporizhzhia', 'Kryvyi Rih'],
                'Moscow': ['Saint Petersburg', 'Nizhny Novgorod', 'Kazan'],
                'Saint Petersburg': ['Moscow', 'Helsinki', 'Tallinn'],
                'Warsaw': ['Krakow', 'Lodz', 'Wroclaw'],
                'Krakow': ['Warsaw', 'Katowice', 'Gdansk'],
                # Add more city mappings as needed
            }
            
            # Get nearby cities list
            nearby = nearby_cities.get(user_city_normalized, [])
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # First try exact city match
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE p.user_id != ? AND p.city_normalized = ?
                    AND dbo.city_normalized = ? AND dbo.date = DATE('now')
                    AND p.user_id NOT IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                    )
                    ORDER BY dbo.order_index
                    LIMIT ?
                ''', (user_id, user_city_normalized, user_city_normalized, user_id, limit))
                
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                # If not enough profiles, try nearby cities
                if len(profiles) < limit and nearby:
                    remaining_limit = limit - len(profiles)
                    placeholders = ','.join(['?' for _ in nearby])
                    
                    cursor.execute(f'''
                        SELECT p.* FROM profiles p
                        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                        WHERE p.user_id != ? AND p.city_normalized IN ({placeholders})
                        AND dbo.city_normalized IN ({placeholders})
                        AND dbo.date = DATE('now')
                        AND p.user_id NOT IN (
                            SELECT to_user_id FROM likes WHERE from_user_id = ?
                        )
                        ORDER BY dbo.order_index
                        LIMIT ?
                    ''', [user_id] + nearby + nearby + [user_id, remaining_limit])
                    
                    nearby_results = cursor.fetchall()
                    profiles.extend([dict(row) for row in nearby_results])
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} (including nearby cities)")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles for swiping nearby: {e}")
            return []

    def get_events_by_city_nearby(self, city: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get events in city and nearby cities"""
        try:
            # Normalize the search city
            city_normalized = self.normalize_city(city)
            logging.info(f"DEBUG: Поиск тусовок в городе и рядом: '{city_normalized}'")
            
            # Define nearby cities mapping
            nearby_cities = {
                'Kyiv': ['Kharkiv', 'Odesa', 'Lviv', 'Dnipro'],
                'Kharkiv': ['Kyiv', 'Poltava', 'Sumy'],
                'Odesa': ['Kyiv', 'Mykolaiv', 'Kherson'],
                'Lviv': ['Kyiv', 'Ivano-Frankivsk', 'Ternopil'],
                'Dnipro': ['Kyiv', 'Zaporizhzhia', 'Kryvyi Rih'],
                'Moscow': ['Saint Petersburg', 'Nizhny Novgorod', 'Kazan'],
                'Saint Petersburg': ['Moscow', 'Helsinki', 'Tallinn'],
                'Warsaw': ['Krakow', 'Lodz', 'Wroclaw'],
                'Krakow': ['Warsaw', 'Katowice', 'Gdansk'],
            }
            
            # Get nearby cities list
            nearby = nearby_cities.get(city_normalized, [])
            all_cities = [city_normalized] + nearby
            
            import datetime
            now = datetime.datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                placeholders = ','.join(['?' for _ in all_cities])
                query = f'''
                    SELECT e.*, p.name as creator_name, COUNT(ep.user_id) as current_members
                    FROM events e
                    JOIN profiles p ON e.creator_id = p.user_id
                    LEFT JOIN event_participants ep ON e.id = ep.event_id
                    WHERE e.city_normalized IN ({placeholders}) AND e.expires_at > ? AND e.status = 'active'
                    GROUP BY e.id
                    ORDER BY e.created_at DESC
                    LIMIT ?
                '''
                params = all_cities + [now, limit]
                
                # Log the query before execution
                self._log_query(query, params, None, "GET_EVENTS_NEARBY")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                events = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Найдено {len(events)} активных тусовок в '{city_normalized}' и рядом")
                return events
                
        except sqlite3.Error as e:
            logging.error(f"Error getting nearby events: {e}")
            return False
    
    def delete_profile(self, user_id: int) -> bool:
        """Delete user profile and all related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete related data
                cursor.execute('DELETE FROM likes WHERE from_user_id = ? OR to_user_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM matches WHERE user1_id = ? OR user2_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM event_participants WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM company_members WHERE user_id = ?', (user_id,))
                
                # Delete events created by user
                cursor.execute('DELETE FROM events WHERE creator_id = ?', (user_id,))
                
                # Delete companies created by user
                cursor.execute('DELETE FROM company_members WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM companies WHERE creator_id = ?', (user_id,))
                
                # Finally delete profile
                cursor.execute('DELETE FROM profiles WHERE user_id = ?', (user_id,))
                
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logging.info(f"DEBUG: Profile {user_id} and all related data deleted successfully")
                else:
                    logging.warning(f"DEBUG: Profile {user_id} deletion affected 0 rows")
                
                return success
                
        except sqlite3.Error as e:
            logging.error(f"ОШИБКА В ШАГЕ DELETE_PROFILE для пользователя {user_id}: {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ DELETE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ DELETE_PROFILE для пользователя {user_id}: Неожиданная ошибка - {e}")
            import traceback
            logging.error(f"ОШИБКА В ШАГЕ DELETE_PROFILE: Traceback - {traceback.format_exc()}")
            return False
    
    def get_profiles_for_swiping_by_city_exact(self, user_id: int, city_normalized: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get profiles for swiping in specific city only (no nearby cities)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE p.user_id != ? 
                    AND p.city_normalized = ?
                    AND dbo.city_normalized = ?
                    AND dbo.date = DATE('now')
                    AND p.user_id NOT IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                    )
                    AND p.user_id NOT IN (
                        SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
                    )
                    AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
                    ORDER BY dbo.order_index
                    LIMIT ?
                ''', (user_id, city_normalized, city_normalized, user_id, user_id, city_normalized, limit))
                
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} in exact city '{city_normalized}'")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles by exact city: {e}")
            return []

    def get_profiles_for_swiping_nearby_by_city(self, user_id: int, city_normalized: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get profiles for swiping in specific city and nearby cities"""
        try:
            # Define nearby cities mapping
            nearby_cities = {
                'Kyiv': ['Kharkiv', 'Odesa', 'Lviv', 'Dnipro'],
                'Kharkiv': ['Kyiv', 'Poltava', 'Sumy'],
                'Odesa': ['Kyiv', 'Mykolaiv', 'Kherson'],
                'Lviv': ['Kyiv', 'Ivano-Frankivsk', 'Ternopil'],
                'Dnipro': ['Kyiv', 'Zaporizhzhia', 'Kryvyi Rih'],
                'Moscow': ['Saint Petersburg', 'Nizhny Novgorod', 'Kazan'],
                'Saint Petersburg': ['Moscow', 'Helsinki', 'Tallinn'],
                'Warsaw': ['Krakow', 'Lodz', 'Wroclaw'],
                'Krakow': ['Warsaw', 'Katowice', 'Gdansk'],
                # Add more city mappings as needed
            }
            
            # Get nearby cities list
            nearby = nearby_cities.get(city_normalized, [])
            all_cities = [city_normalized] + nearby
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                placeholders = ','.join(['?' for _ in all_cities])
                query = f'''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE p.user_id != ? AND p.city_normalized IN ({placeholders})
                    AND dbo.city_normalized IN ({placeholders})
                    AND dbo.date = DATE('now')
                    AND p.user_id NOT IN (
                        SELECT to_user_id FROM likes WHERE from_user_id = ?
                    )
                    ORDER BY dbo.order_index
                    LIMIT ?
                '''
                params = [user_id] + all_cities + all_cities + [user_id, limit]
                
                # Log the query before execution
                self._log_query(query, params, user_id, "GET_PROFILES_BY_CITY")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} in city '{city_normalized}' and nearby")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles by city: {e}")
            return []

    def save_user_filters(self, user_id: int, gender_filter: str = None, who_pays_filter: str = None) -> bool:
        """Save user's dating filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if gender_filter is not None:
                    updates.append("filter_gender = ?")
                    params.append(gender_filter)
                
                if who_pays_filter is not None:
                    updates.append("filter_who_pays = ?")
                    params.append(who_pays_filter)
                
                if updates:
                    params.append(user_id)
                    query = f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount > 0
                
                return False
        except sqlite3.Error as e:
            logging.error(f"Error saving user filters: {e}")
            return False
    
    def get_user_filters(self, user_id: int) -> Dict[str, str]:
        """Get user's dating filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'gender': result['filter_gender'] or 'all',
                        'who_pays': result['filter_who_pays'] or 'any'
                    }
                return {'gender': 'all', 'who_pays': 'any'}
        except sqlite3.Error as e:
            logging.error(f"Error getting user filters: {e}")
            return {'gender': 'all', 'who_pays': 'any'}

    def mark_profile_as_viewed(self, user_id: int, profile_id: int) -> bool:
        """Mark a profile as viewed for today"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO profile_views (user_id, profile_id, view_date)
                    VALUES (?, ?, DATE('now'))
                ''', (user_id, profile_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error marking profile as viewed: {e}")
            return False
    
    def get_viewed_profiles_today(self, user_id: int) -> List[int]:
        """Get list of profile IDs viewed today"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT profile_id FROM profile_views 
                    WHERE user_id = ? AND view_date = DATE('now')
                ''', (user_id,))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error getting viewed profiles: {e}")
            return []

    def get_profiles_for_swiping_exact_city_all_data(self, user_id: int, city_normalized: str, gender_filter: str = None, who_pays_filter: str = None) -> List[Dict[str, Any]]:
        """Get profiles for swiping in exact city only with filters - optimized version"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build WHERE conditions for exact city only
                conditions = [
                    "p.user_id != ?", 
                    "p.city_normalized = ?",
                    "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)",
                    "p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))",
                    "(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))"
                ]
                params = [user_id, city_normalized, user_id, user_id, city_normalized]
                
                # Add gender filter
                if gender_filter and gender_filter != 'all':
                    conditions.append("p.gender = ?")
                    params.append(gender_filter)
                
                # Add who pays filter
                if who_pays_filter and who_pays_filter != 'any':
                    who_pays_mapping = {
                        'i_treat': 'i_treat',
                        'you_treat': 'someone_treats',
                        'split': 'each_self',
                        'any': None
                    }
                    if who_pays_filter in who_pays_mapping and who_pays_mapping[who_pays_filter]:
                        conditions.append("p.who_pays = ?")
                        params.append(who_pays_mapping[who_pays_filter])
                
                query = f'''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE {' AND '.join(conditions)}
                    AND dbo.city_normalized = ?
                    AND dbo.date = DATE('now')
                    ORDER BY dbo.order_index
                    LIMIT 10
                '''
                
                params.append(city_normalized)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} in exact city '{city_normalized}' with filters (optimized)")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles by exact city with filters (optimized): {e}")
            return []

    def get_profiles_for_swiping_exact_city(self, user_id: int, city_normalized: str, gender_filter: str = None, who_pays_filter: str = None) -> List[Dict[str, Any]]:
        """Get profiles for swiping in exact city only with daily limits"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check daily limits first
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Get city limit
                city_limits = {
                    "Kyiv": 15, "Moscow": 15, "Saint Petersburg": 12, "Minsk": 12,
                    "Novosibirsk": 10, "Yekaterinburg": 10, "Tashkent": 10, "Kazan": 10,
                    "Kharkiv": 10, "Nizhny Novgorod": 10, "Chelyabinsk": 10, "Almaty": 10,
                    "Samara": 10, "Ufa": 10, "Rostov-on-Don": 10, "Krasnoyarsk": 10,
                    "Omsk": 10, "Voronezh": 10, "Perm": 10, "Volgograd": 10,
                    "Odesa": 8, "Krasnodar": 8, "Dnipro": 8, "Saratov": 8, "Donetsk": 8,
                    "Tyumen": 8, "Tolyatti": 8, "Lviv": 8, "Zaporizhzhia": 8, "Izhevsk": 8,
                    "Barnaul": 8, "Ulyanovsk": 8, "Irkutsk": 8, "Khabarovsk": 8, "Makhachkala": 8,
                    "Vladivostok": 8, "Yaroslavl": 8, "Orenburg": 8, "Tomsk": 8, "Kemerovo": 8,
                    "Ryazan": 8, "Naberezhnye Chelny": 8, "Astana": 8, "Penza": 8, "Kirov": 8,
                    "Lipetsk": 8, "Cheboksary": 8, "Balashikha": 8, "Mykolaiv": 8,
                    "default": 5
                }
                
                daily_limit = city_limits.get(city_normalized, city_limits["default"])
                
                # Check current daily usage
                cursor.execute('''
                    SELECT bots_shown FROM daily_bot_limits 
                    WHERE user_id = ? AND city_normalized = ? AND date = ?
                ''', (user_id, city_normalized, today))
                
                result = cursor.fetchone()
                
                if result:
                    bots_shown = result[0]
                    if bots_shown >= daily_limit:
                        logging.info(f"User {user_id} reached daily limit of {daily_limit} bots in {city_normalized}")
                        return []  # No more bots today
                    remaining_limit = daily_limit - bots_shown
                else:
                    # Create new daily limit record
                    cursor.execute('''
                        INSERT INTO daily_bot_limits (user_id, city_normalized, date, daily_limit)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, city_normalized, today, daily_limit))
                    remaining_limit = daily_limit
                
                # Adjust query limit to remaining bots
                actual_limit = min(10, remaining_limit)
                
                # Build WHERE conditions for exact city only
                conditions = [
                    "p.user_id != ?", 
                    "p.city_normalized = ?",
                    "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)",
                    "p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))",
                    "(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))"
                ]
                params = [user_id, city_normalized, user_id, user_id, city_normalized]
                
                # Add gender filter
                if gender_filter and gender_filter != 'all':
                    conditions.append("p.gender = ?")
                    params.append(gender_filter)
                
                # Add who pays filter
                if who_pays_filter and who_pays_filter != 'any':
                    who_pays_mapping = {
                        'i_treat': 'i_treat',
                        'you_treat': 'someone_treats',
                        'split': 'each_self',
                        'any': None
                    }
                    if who_pays_filter in who_pays_mapping and who_pays_mapping[who_pays_filter]:
                        conditions.append("p.who_pays = ?")
                        params.append(who_pays_mapping[who_pays_filter])
                
                query = f'''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE {' AND '.join(conditions)}
                    AND dbo.city_normalized = ?
                    AND dbo.date = DATE('now')
                    ORDER BY dbo.order_index
                    LIMIT ?
                '''
                
                params.extend([city_normalized, actual_limit])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} in exact city '{city_normalized}' with filters (limit: {actual_limit})")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles by exact city with filters: {e}")
            return []

    def increment_daily_bot_count(self, user_id: int, city_normalized: str) -> bool:
        """Increment daily bot counter for user"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update or insert daily limit record
                cursor.execute('''
                    UPDATE daily_bot_limits 
                    SET bots_shown = bots_shown + 1
                    WHERE user_id = ? AND city_normalized = ? AND date = ?
                ''', (user_id, city_normalized, today))
                
                if cursor.rowcount == 0:
                    # Create new record if doesn't exist
                    city_limits = {
                        "Kyiv": 15, "Moscow": 15, "Saint Petersburg": 12, "Minsk": 12,
                        "Novosibirsk": 10, "Yekaterinburg": 10, "Tashkent": 10, "Kazan": 10,
                        "Kharkiv": 10, "Nizhny Novgorod": 10, "Chelyabinsk": 10, "Almaty": 10,
                        "Samara": 10, "Ufa": 10, "Rostov-on-Don": 10, "Krasnoyarsk": 10,
                        "Omsk": 10, "Voronezh": 10, "Perm": 10, "Volgograd": 10,
                        "Odesa": 8, "Krasnodar": 8, "Dnipro": 8, "Saratov": 8, "Donetsk": 8,
                        "Tyumen": 8, "Tolyatti": 8, "Lviv": 8, "Zaporizhzhia": 8, "Izhevsk": 8,
                        "Barnaul": 8, "Ulyanovsk": 8, "Irkutsk": 8, "Khabarovsk": 8, "Makhachkala": 8,
                        "Vladivostok": 8, "Yaroslavl": 8, "Orenburg": 8, "Tomsk": 8, "Kemerovo": 8,
                        "Ryazan": 8, "Naberezhnye Chelny": 8, "Astana": 8, "Penza": 8, "Kirov": 8,
                        "Lipetsk": 8, "Cheboksary": 8, "Balashikha": 8, "Mykolaiv": 8,
                        "default": 5
                    }
                    
                    daily_limit = city_limits.get(city_normalized, city_limits["default"])
                    
                    cursor.execute('''
                        INSERT INTO daily_bot_limits (user_id, city_normalized, date, daily_limit, bots_shown)
                        VALUES (?, ?, ?, ?, 1)
                    ''', (user_id, city_normalized, today, daily_limit))
                
                conn.commit()
                logging.info(f"Incremented daily bot count for user {user_id} in {city_normalized}")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error incrementing daily bot count: {e}")
            return False

    def get_daily_bot_status(self, user_id: int, city_normalized: str) -> Dict[str, Any]:
        """Get daily bot status for user"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT bots_shown, daily_limit FROM daily_bot_limits 
                    WHERE user_id = ? AND city_normalized = ? AND date = ?
                ''', (user_id, city_normalized, today))
                
                result = cursor.fetchone()
                
                if result:
                    bots_shown, daily_limit = result
                    remaining = max(0, daily_limit - bots_shown)
                    return {
                        "shown": bots_shown,
                        "limit": daily_limit,
                        "remaining": remaining,
                        "reached_limit": bots_shown >= daily_limit
                    }
                else:
                    # New user - get default limit
                    city_limits = {
                        "Kyiv": 15, "Moscow": 15, "Saint Petersburg": 12, "Minsk": 12,
                        "Novosibirsk": 10, "Yekaterinburg": 10, "Tashkent": 10, "Kazan": 10,
                        "Kharkiv": 10, "Nizhny Novgorod": 10, "Chelyabinsk": 10, "Almaty": 10,
                        "Samara": 10, "Ufa": 10, "Rostov-on-Don": 10, "Krasnoyarsk": 10,
                        "Omsk": 10, "Voronezh": 10, "Perm": 10, "Volgograd": 10,
                        "Odesa": 8, "Krasnodar": 8, "Dnipro": 8, "Saratov": 8, "Donetsk": 8,
                        "Tyumen": 8, "Tolyatti": 8, "Lviv": 8, "Zaporizhzhia": 8, "Izhevsk": 8,
                        "Barnaul": 8, "Ulyanovsk": 8, "Irkutsk": 8, "Khabarovsk": 8, "Makhachkala": 8,
                        "Vladivostok": 8, "Yaroslavl": 8, "Orenburg": 8, "Tomsk": 8, "Kemerovo": 8,
                        "Ryazan": 8, "Naberezhnye Chelny": 8, "Astana": 8, "Penza": 8, "Kirov": 8,
                        "Lipetsk": 8, "Cheboksary": 8, "Balashikha": 8, "Mykolaiv": 8,
                        "default": 5
                    }
                    
                    daily_limit = city_limits.get(city_normalized, city_limits["default"])
                    
                    return {
                        "shown": 0,
                        "limit": daily_limit,
                        "remaining": daily_limit,
                        "reached_limit": False
                    }
                
        except sqlite3.Error as e:
            logging.error(f"Error getting daily bot status: {e}")
            return {
                "shown": 0,
                "limit": 5,
                "remaining": 5,
                "reached_limit": False
            }

    def get_profiles_for_swiping_with_filters(self, user_id: int, city_normalized: str = None, gender_filter: str = None, who_pays_filter: str = None) -> List[Dict[str, Any]]:
        """Get profiles for swiping with premium filters applied"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build WHERE conditions
                conditions = ["p.user_id != ?", "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)"]
                params = [user_id, user_id]
                
                # Exclude profiles viewed today
                conditions.append("p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))")
                params.append(user_id)
                
                # Add city filter
                if city_normalized:
                    # For real users: include nearby cities for premium users
                    # For bots: only show in their own city
                    nearby_cities = {
                        'Kyiv': ['Kharkiv', 'Odesa', 'Lviv', 'Dnipro'],
                        'Kharkiv': ['Kyiv', 'Poltava', 'Sumy'],
                        'Odesa': ['Kyiv', 'Mykolaiv', 'Kherson'],
                        'Lviv': ['Kyiv', 'Ivano-Frankivsk', 'Ternopil'],
                        'Dnipro': ['Kyiv', 'Zaporizhzhia', 'Kryvyi Rih'],
                    }
                    
                    # Separate logic for real users vs bots
                    # For real users: include nearby cities
                    # For bots: only their own city
                    all_cities = [city_normalized] + nearby_cities.get(city_normalized, [])
                    city_placeholders = ','.join(['?' for _ in all_cities])
                    conditions.append(f"p.city_normalized IN ({city_placeholders})")
                    params.extend(all_cities)
                    
                    # Add additional condition: if it's a bot, only show in their own city AND only if active today
                    conditions.append("(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))")
                    params.append(city_normalized)
                
                # Add gender filter
                if gender_filter and gender_filter != 'all':
                    conditions.append("p.gender = ?")
                    params.append(gender_filter)
                
                # Add who pays filter
                if who_pays_filter and who_pays_filter != 'any':
                    who_pays_mapping = {
                        'i_treat': 'i_treat',
                        'you_treat': 'someone_treats',
                        'split': 'each_self',
                        'any': None
                    }
                    if who_pays_filter in who_pays_mapping and who_pays_mapping[who_pays_filter]:
                        conditions.append("p.who_pays = ?")
                        params.append(who_pays_mapping[who_pays_filter])
                
                query = f'''
                    SELECT p.* FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE {' AND '.join(conditions)}
                    AND dbo.city_normalized = p.city_normalized
                    AND dbo.date = DATE('now')
                    ORDER BY dbo.order_index
                    LIMIT 10
                '''
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                profiles = [dict(row) for row in results]
                
                logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} with filters: gender={gender_filter}, who_pays={who_pays_filter}")
                return profiles
                
        except sqlite3.Error as e:
            logging.error(f"Error getting profiles with filters: {e}")
            return []

# Global database instance
db = Database()
