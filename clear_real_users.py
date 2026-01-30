import sqlite3
from datetime import datetime

def clear_real_users():
    """Очистка всех реальных пользователей из базы данных"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CLEARING REAL USERS FROM DATABASE:")
    print("=" * 60)
    
    # 1. Проверяем текущее состояние
    print(f"\n1. CURRENT DATABASE STATUS:")
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 0")
    real_users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 1")
    bot_users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles")
    total_users_count = cursor.fetchone()[0]
    
    print(f"   Total profiles: {total_users_count}")
    print(f"   Real users: {real_users_count}")
    print(f"   Bot users: {bot_users_count}")
    
    # 2. Показываем реальных пользователей перед удалением
    print(f"\n2. REAL USERS TO BE DELETED:")
    
    cursor.execute('''
        SELECT user_id, name, city, created_at FROM profiles 
        WHERE is_bot = 0 
        ORDER BY created_at DESC
    ''')
    
    real_users = cursor.fetchall()
    
    if real_users:
        print(f"   Found {len(real_users)} real users:")
        for user_id, name, city, created_at in real_users:
            print(f"     ID: {user_id}, Name: {name}, City: {city}, Created: {created_at}")
    else:
        print("   No real users found")
    
    # 3. Удаляем связанные данные реальных пользователей
    print(f"\n3. DELETING RELATED DATA:")
    
    tables_to_clean = [
        ("profile_views", "user_id"),
        ("likes", "from_user_id"),
        ("likes", "to_user_id"),
        ("daily_bot_limits", "user_id"),
        ("user_notifications", "user_id"),
        ("companies", "creator_id"),
        ("company_members", "user_id"),
        ("events", "creator_id"),
        ("event_participants", "user_id")
    ]
    
    for table, column in tables_to_clean:
        # Сначала проверяем сколько записей
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute(f"DELETE FROM {table} WHERE {column} IN (SELECT user_id FROM profiles WHERE is_bot = 0)")
            print(f"   ✅ Deleted {count} records from {table}")
        else:
            print(f"   - No records to delete from {table}")
    
    # 4. Удаляем профили реальных пользователей
    print(f"\n4. DELETING REAL USER PROFILES:")
    
    cursor.execute("DELETE FROM profiles WHERE is_bot = 0")
    deleted_profiles = cursor.rowcount
    print(f"   ✅ Deleted {deleted_profiles} real user profiles")
    
    # 5. Проверяем результат
    print(f"\n5. VERIFICATION:")
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 0")
    remaining_real = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 1")
    remaining_bots = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles")
    remaining_total = cursor.fetchone()[0]
    
    print(f"   Remaining real users: {remaining_real}")
    print(f"   Remaining bot users: {remaining_bots}")
    print(f"   Remaining total: {remaining_total}")
    
    # 6. Создаем бэкап перед очисткой
    print(f"\n6. CREATING BACKUP:")
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_file = f'drink_bot_before_real_users_clear_{timestamp}.db'
    
    try:
        import shutil
        shutil.copy2('drink_bot.db', backup_file)
        print(f"   ✅ Backup created: {backup_file}")
    except Exception as e:
        print(f"   ❌ Error creating backup: {e}")
    
    # 7. Статистика после очистки
    print(f"\n7. POST-CLEANUP STATISTICS:")
    
    stats_tables = [
        ("profiles", "Total profiles"),
        ("profile_views", "Profile views"),
        ("likes", "Likes"),
        ("daily_bot_limits", "Daily limits"),
        ("user_notifications", "Notifications"),
        ("companies", "Companies"),
        ("events", "Events")
    ]
    
    for table, description in stats_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {description}: {count}")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("REAL USERS CLEANUP COMPLETE!")
    print("\nSUMMARY:")
    print(f"✅ Deleted {deleted_profiles} real user profiles")
    print(f"✅ Cleaned all related data")
    print(f"✅ Preserved {remaining_bots} bot profiles")
    print(f"✅ Created backup: {backup_file}")
    
    print(f"\nDATABASE READY FOR:")
    print("🔄 Repository update")
    print("🚀 GitHub deployment")
    print("🧪 Fresh testing")
    
    print(f"\nNEXT STEPS:")
    print("1. Update repository with cleaned database")
    print("2. Commit changes to GitHub")
    print("3. Deploy to production")
    print("4. Test with fresh real users")

if __name__ == "__main__":
    clear_real_users()
