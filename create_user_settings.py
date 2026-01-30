import sqlite3

def create_user_settings_table():
    """Create user_settings table for storing preferences before profile creation"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CREATING USER_SETTINGS TABLE:")
    print("=" * 50)
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("✅ user_settings table already exists")
    else:
        # Create table
        cursor.execute('''
            CREATE TABLE user_settings (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("✅ Created user_settings table")
    
    # Create function to get user language
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'ru',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ User settings system ready")

if __name__ == "__main__":
    create_user_settings_table()
