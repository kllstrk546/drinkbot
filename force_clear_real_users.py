import sqlite3
from datetime import datetime

def force_clear_real_users():
    """Принудительная очистка реальных пользователей"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("FORCE CLEARING REAL USERS:")
    print("=" * 50)
    
    # 1. Удаляем связанные данные
    print("Deleting related data...")
    
    # Profile views
    cursor.execute("DELETE FROM profile_views WHERE user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted profile views")
    
    # Likes (from)
    cursor.execute("DELETE FROM likes WHERE from_user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted likes from real users")
    
    # Likes (to)
    cursor.execute("DELETE FROM likes WHERE to_user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted likes to real users")
    
    # Daily limits
    cursor.execute("DELETE FROM daily_bot_limits WHERE user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted daily limits")
    
    # Notifications
    cursor.execute("DELETE FROM user_notifications WHERE user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted notifications")
    
    # Companies
    cursor.execute("DELETE FROM companies WHERE creator_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted companies")
    
    # Company members
    cursor.execute("DELETE FROM company_members WHERE user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted company members")
    
    # Events
    cursor.execute("DELETE FROM events WHERE creator_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted events")
    
    # Event participants
    cursor.execute("DELETE FROM event_participants WHERE user_id IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
    print("Deleted event participants")
    
    # 2. Удаляем профили реальных пользователей
    print("Deleting real user profiles...")
    cursor.execute("DELETE FROM profiles WHERE is_bot = 0")
    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} real user profiles")
    
    # 3. Проверяем результат
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 0")
    remaining_real = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 1")
    remaining_bots = cursor.fetchone()[0]
    
    print(f"Remaining real users: {remaining_real}")
    print(f"Remaining bot users: {remaining_bots}")
    
    # 4. Создаем бэкап
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = f'drink_bot_after_real_users_clear_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2('drink_bot.db', backup_file)
        print(f"Backup created: {backup_file}")
    except Exception as e:
        print(f"Error creating backup: {e}")
    
    conn.commit()
    conn.close()
    
    print("=" * 50)
    print("FORCE CLEANUP COMPLETE!")
    print(f"Deleted {deleted_count} real users")
    print(f"Remaining {remaining_bots} bot users")

if __name__ == "__main__":
    force_clear_real_users()
