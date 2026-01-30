import sqlite3
from datetime import datetime
import shutil
import os

def backup_all_data():
    """Создание полной резервной копии базы данных"""
    
    print("BACKING UP ALL DATA:")
    print("=" * 50)
    
    # 1. Проверяем текущую базу
    db_path = 'drink_bot.db'
    
    if not os.path.exists(db_path):
        print(f"   ERROR: Database file {db_path} not found!")
        return
    
    print(f"   Found database: {db_path}")
    
    # 2. Создаем временную копию
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_path = f'drink_bot_backup_{timestamp}.db'
    
    print(f"\n2. CREATING BACKUP:")
    print(f"   Source: {db_path}")
    print(f"   Backup: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"   ✅ Backup created successfully!")
        
        # Проверяем размер
        original_size = os.path.getsize(db_path)
        backup_size = os.path.getsize(backup_path)
        
        print(f"   Original size: {original_size:,} bytes")
        print(f"   Backup size: {backup_size:,} bytes")
        
        if original_size == backup_size:
            print(f"   ✅ Backup verified - sizes match")
        else:
            print(f"   ⚠️  WARNING: Size mismatch!")
        
    except Exception as e:
        print(f"   ❌ Error creating backup: {e}")
        return
    
    # 3. Создаем SQL дамп
    print(f"\n3. CREATING SQL DUMP:")
    
    sql_dump_path = f'drink_bot_backup_{timestamp}.sql'
    
    try:
        conn = sqlite3.connect(db_path)
        
        with open(sql_dump_path, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        print(f"   ✅ SQL dump created: {sql_dump_path}")
        
        # Проверяем размер
        dump_size = os.path.getsize(sql_dump_path)
        print(f"   Dump size: {dump_size:,} bytes")
        
    except Exception as e:
        print(f"   ❌ Error creating SQL dump: {e}")
    
    # 4. Статистика таблиц
    print(f"\n4. TABLE STATISTICS:")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"   Total tables: {len(tables)}")
        
        table_stats = []
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_stats.append((table_name, count))
        
        print(f"\n   Table statistics:")
        for table, count in sorted(table_stats):
            print(f"     {table}: {count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error getting table stats: {e}")
    
    # 5. Проверяем важные данные
    print(f"\n5. IMPORTANT DATA VERIFICATION:")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем профили
        cursor.execute("SELECT COUNT(*) FROM profiles")
        total_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 1")
        bot_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 0")
        real_profiles = cursor.fetchone()[0]
        
        print(f"   Total profiles: {total_profiles}")
        print(f"   Bot profiles: {bot_profiles}")
        print(f"   Real profiles: {real_profiles}")
        
        # Проверяем daily_bot_order
        cursor.execute("SELECT COUNT(*) FROM daily_bot_order")
        order_entries = cursor.fetchone()[0]
        
        print(f"   Daily order entries: {order_entries}")
        
        # Проверяем daily_bot_limits
        cursor.execute("SELECT COUNT(*) FROM daily_bot_limits")
        limit_entries = cursor.fetchone()[0]
        
        print(f"   Daily limit entries: {limit_entries}")
        
        # Проверяем profile_views
        cursor.execute("SELECT COUNT(*) FROM profile_views")
        view_entries = cursor.fetchone()[0]
        
        print(f"   Profile views: {view_entries}")
        
        # Проверяем лайки
        cursor.execute("SELECT COUNT(*) FROM likes")
        like_entries = cursor.fetchone()[0]
        
        print(f"   Likes: {like_entries}")
        
        # Проверяем уведомления
        cursor.execute("SELECT COUNT(*) FROM user_notifications")
        notification_entries = cursor.fetchone()[0]
        
        print(f"   Notifications: {notification_entries}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verifying data: {e}")
    
    # 6. Архивация старых бэкапов
    print(f"\n6. ARCHIVING OLD BACKUPS:")
    
    backup_files = []
    for file in os.listdir('.'):
        if file.startswith('drink_bot_backup_') and file.endswith('.db'):
            backup_files.append(file)
    
    if backup_files:
        print(f"   Found {len(backup_files)} old backup files:")
        
        # Удаляем старые бэкапы (оставляем последние 5)
        backup_files.sort()
        old_backups = backup_files[:-5] if len(backup_files) > 5 else []
        
        for old_backup in old_backups:
            try:
                os.remove(old_backup)
                print(f"   🗑️ Deleted old backup: {old_backup}")
            except Exception as e:
                print(f"   ⚠️  Error deleting {old_backup}: {e}")
        
        # Показываем оставшиеся
        remaining_backups = backup_files[-5:] if len(backup_files) > 5 else backup_files
        print(f"   Keeping {len(remaining_backups)} recent backups:")
        
        for backup in remaining_backups:
            size = os.path.getsize(backup)
            mtime = os.path.getmtime(backup)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"     {backup} ({size:,} bytes, {mtime_str})")
    else:
        print("   No old backup files found")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("BACKUP COMPLETE!")
    print("\nFILES CREATED:")
    print(f"1. Database backup: {backup_path}")
    print(f"2. SQL dump: {sql_dump_path}")
    
    print(f"\nDATA SUMMARY:")
    print(f"✅ Profiles: {total_profiles} (Bots: {bot_profiles}, Real: {real_profiles})")
    print(f"✅ Daily order: {order_entries} entries")
    print(f"✅ Daily limits: {limit_entries} entries")
    print(f"✅ Profile views: {view_entries} entries")
    print(f"✅ Likes: {like_entries} entries")
    print(f"✅ Notifications: {notification_entries} entries")
    
    print(f"\nBACKUP LOCATION: {os.path.abspath(backup_path)}")
    print(f"SQL DUMP LOCATION: {os.path.abspath(sql_dump_path)}")
    
    print("\n✅ All data backed up successfully!")
    print("🗄️ Old backups archived (keeping last 5)")

if __name__ == "__main__":
    backup_all_data()
