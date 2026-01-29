import sqlite3
from datetime import datetime, timedelta

def check_bot_rotation_schedule():
    """Проверяем расписание обновления ботов"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CHECKING BOT ROTATION SCHEDULE:")
    print("=" * 60)
    
    # 1. Проверяем last_rotation_date distribution
    print(f"\n1. ROTATION DATES DISTRIBUTION:")
    cursor.execute('''
        SELECT last_rotation_date, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1
        GROUP BY last_rotation_date
        ORDER BY last_rotation_date DESC
        LIMIT 10
    ''')
    
    rotation_dates = cursor.fetchall()
    for date, count in rotation_dates:
        print(f"   {date}: {count} bots")
    
    # 2. Проверяем сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n2. TODAY'S ROTATION ({today}):")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 10
    ''', (today,))
    
    today_cities = cursor.fetchall()
    print(f"   Cities with bots today: {len(today_cities)}")
    for city, count in today_cities:
        print(f"     {city}: {count} bots")
    
    # 3. Проверяем вчерашний день
    print(f"\n3. YESTERDAY'S ROTATION ({yesterday}):")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 10
    ''', (yesterday,))
    
    yesterday_cities = cursor.fetchall()
    print(f"   Cities with bots yesterday: {len(yesterday_cities)}")
    for city, count in yesterday_cities:
        print(f"     {city}: {count} bots")
    
    # 4. Проверяем daily_bot_order
    print(f"\n4. DAILY_BOT_ORDER DATES:")
    cursor.execute('''
        SELECT date, COUNT(DISTINCT city_normalized) as cities, COUNT(*) as total_bots
        FROM daily_bot_order 
        GROUP BY date
        ORDER BY date DESC
        LIMIT 10
    ''')
    
    order_dates = cursor.fetchall()
    for date, cities, total_bots in order_dates:
        print(f"   {date}: {cities} cities, {total_bots} total bots")
    
    # 5. Проверяем время создания/обновления
    print(f"\n5. ROTATION TIME CHECK:")
    
    # Проверяем есть ли скрипты для ротации
    import os
    script_files = [
        'daily_rotation.py',
        'setup_daily_system.py', 
        'create_filtered_daily_order.py',
        'fix_daily_stability.py'
    ]
    
    print("   Rotation scripts found:")
    for script in script_files:
        if os.path.exists(script):
            print(f"     OK {script}")
        else:
            print(f"     NO {script}")
    
    # 6. Проверяем автоматическую ротацию
    print(f"\n6. AUTOMATIC ROTATION CHECK:")
    print("   Current system requires manual execution:")
    print("   - python daily_rotation.py (once per day)")
    print("   - python setup_daily_system.py (once per day)")
    print("   - python create_filtered_daily_order.py (once per day)")
    
    # 7. Проверяем что должно быть по логике
    print(f"\n7. EXPECTED ROTATION LOGIC:")
    print("   - Rotation should happen once per day")
    print("   - Usually at midnight (00:00)")
    print("   - New bots get last_rotation_date = today")
    print("   - Old bots get last_rotation_date = NULL or old date")
    print("   - Only bots with last_rotation_date = today are active")
    
    # 8. Проверяем сколько ботов должно быть активно
    print(f"\n8. EXPECTED ACTIVE BOTS:")
    
    # Таблица ожидаемых количеств по городам
    expected_counts = {
        "Tier 1": {"cities": ["Kyiv", "Moscow", "Saint Petersburg", "Minsk"], "per_gender": 15},
        "Tier 2": {"cities": ["Novosibirsk", "Yekaterinburg", "Tashkent", "Kazan", "Kharkiv", "Nizhny Novgorod", "Chelyabinsk", "Almaty", "Samara", "Ufa", "Rostov-on-Don", "Krasnoyarsk", "Omsk", "Voronezh", "Perm", "Volgograd"], "per_gender": 10},
        "Tier 3": {"cities": ["Odesa", "Krasnodar", "Dnipro", "Saratov", "Donetsk", "Tyumen", "Tolyatti", "Lviv", "Zaporizhzhia", "Izhevsk", "Barnaul", "Ulyanovsk", "Irkutsk", "Khabarovsk", "Makhachkala", "Vladivostok"], "per_gender": 7},
        "Tier 4": {"cities": ["Yaroslavl", "Orenburg", "Tomsk", "Kemerovo", "Ryazan", "Naberezhnye Chelny", "Astana", "Penza", "Kirov", "Lipetsk", "Cheboksary", "Balashikha", "Mykolaiv"], "per_gender": 5}
    }
    
    total_expected = 0
    for tier, config in expected_counts.items():
        tier_total = len(config["cities"]) * config["per_gender"] * 2  # *2 for male+female
        total_expected += tier_total
        print(f"   {tier}: {len(config['cities'])} cities x {config['per_gender']} per gender x 2 genders = {tier_total}")
    
    print(f"   Total expected active bots: {total_expected}")
    
    # 9. Сравниваем с реальностью
    print(f"\n9. REALITY CHECK:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
    ''', (today,))
    
    actual_active = cursor.fetchone()[0]
    print(f"   Actual active bots today: {actual_active}")
    print(f"   Expected active bots: {total_expected}")
    print(f"   Difference: {actual_active - total_expected}")
    
    # 10. Рекомендации
    print(f"\n10. RECOMMENDATIONS:")
    if actual_active == total_expected:
        print("   OK Bot count matches expectations")
        print("   OK Rotation system is working correctly")
    else:
        print("   WARNING Bot count doesn't match expectations")
        print("   WARNING Check rotation scripts")
    
    print("\n   TO AUTOMATE ROTATION:")
    print("   1. Set up cron job to run daily at 00:00")
    print("   2. Command: python create_filtered_daily_order.py")
    print("   3. Or use task scheduler on Windows")
    print("   4. Or add rotation to bot startup")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("ROTATION SCHEDULE CHECK COMPLETE!")

if __name__ == "__main__":
    check_bot_rotation_schedule()
