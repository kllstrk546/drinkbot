import sqlite3
from datetime import datetime, timedelta

def analyze_current_rotation():
    """Анализируем текущую систему ротации"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - 
                 timedelta(days=1)).strftime('%Y-%m-%d')
    
    print("ANALYZING CURRENT ROTATION SYSTEM:")
    print("=" * 60)
    
    # 1. Проверяем last_rotation_date distribution
    print(f"\n1. ROTATION DATES (today={today}, yesterday={yesterday}):")
    cursor.execute('''
        SELECT last_rotation_date, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1
        GROUP BY last_rotation_date
        ORDER BY last_rotation_date DESC
        LIMIT 5
    ''')
    
    rotation_dates = cursor.fetchall()
    for date, count in rotation_dates:
        print(f"   {date}: {count} bots")
    
    # 2. Проверяем активных ботов сегодня в Киеве
    print(f"\n2. KYIV ACTIVE BOTS (last_rotation_date = {today}):")
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND last_rotation_date = ?
        ORDER BY gender, user_id
    ''', (today,))
    
    kyiv_active_today = cursor.fetchall()
    print(f"   Active today: {len(kyiv_active_today)}")
    
    male_count = len([b for b in kyiv_active_today if b[2] == 'male'])
    female_count = len([b for b in kyiv_active_today if b[2] == 'female'])
    print(f"   Male: {male_count}, Female: {female_count}")
    
    # 3. Проверяем неактивных ботов в Киеве
    print(f"\n3. KYIV INACTIVE BOTS (last_rotation_date != {today}):")
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND last_rotation_date != ?
        ORDER BY last_rotation_date DESC, gender, user_id
        LIMIT 10
    ''', (today,))
    
    kyiv_inactive = cursor.fetchall()
    print(f"   Inactive today: {len(kyiv_inactive)}")
    
    for bot in kyiv_inactive[:5]:
        user_id, name, gender, photo_id, rotation_date = bot
        print(f"   {name} ({gender}) - last active: {rotation_date}")
    
    # 4. Проверяем сколько всего ботов в Киеве
    print(f"\n4. TOTAL KYIV BOTS:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv'
    ''')
    
    total_kyiv = cursor.fetchone()[0]
    print(f"   Total in Kyiv: {total_kyiv}")
    print(f"   Active today: {len(kyiv_active_today)}")
    print(f"   Inactive today: {total_kyiv - len(kyiv_active_today)}")
    
    # 5. Проверяем stability - те ли боты показываются
    print(f"\n5. STABILITY CHECK:")
    
    # Проверяем есть ли дубликаты photo_id у активных ботов
    cursor.execute('''
        SELECT photo_id, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND last_rotation_date = ?
        AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY photo_id
        HAVING count > 1
        ORDER BY count DESC
    ''', (today,))
    
    duplicate_photos = cursor.fetchall()
    if duplicate_photos:
        print(f"   Duplicate photos among active bots: {len(duplicate_photos)}")
        for photo_id, count in duplicate_photos[:3]:
            print(f"     {photo_id[:30]}... used {count} times")
    else:
        print("   No duplicate photos among active bots")
    
    # 6. Проверяем consistency в других городах
    print(f"\n6. OTHER CITIES ACTIVE BOTS:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 5
    ''', (today,))
    
    cities_active = cursor.fetchall()
    for city, count in cities_active:
        print(f"   {city}: {count} active bots")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("\nRECOMMENDATIONS:")
    print("1. Active bots should be consistent throughout the day")
    print("2. Rotation should happen once per day")
    print("3. Same bots should appear for all users in the same city")

if __name__ == "__main__":
    analyze_current_rotation()
