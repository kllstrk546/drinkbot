import sqlite3
from datetime import datetime

def debug_city_switch_hang():
    """Диагностика зависания при смене города"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    
    print("DEBUGGING CITY SWITCH HANG:")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"Date: {today}")
    
    # 1. Проверяем FSM state пользователя
    print(f"\n1. FSM STATE CHECK:")
    print("   Checking if user has active state...")
    
    # В реальной ситуации здесь нужно проверять FSM state через aiogram
    # Но мы можем проверить profile_views и другие признаки
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    today_views = cursor.fetchone()[0]
    print(f"   Today's profile views: {today_views}")
    
    # 2. Проверяем последние действия пользователя
    print(f"\n2. RECENT ACTIVITY CHECK:")
    cursor.execute('''
        SELECT profile_id, view_date
        FROM profile_views 
        WHERE user_id = ? 
        ORDER BY view_date DESC
        LIMIT 5
    ''', (user_id,))
    
    recent_views = cursor.fetchall()
    print(f"   Recent profile views:")
    for profile_id, view_date in recent_views:
        cursor.execute('SELECT name, city_normalized FROM profiles WHERE user_id = ?', (profile_id,))
        profile_info = cursor.fetchone()
        if profile_info:
            name, city = profile_info
            print(f"     {name} ({city}) at {view_date}")
    
    # 3. Проверяем город пользователя
    print(f"\n3. USER CITY CHECK:")
    cursor.execute('''
        SELECT city, city_normalized, city_display
        FROM profiles 
        WHERE user_id = ? AND is_bot = 0
    ''', (user_id,))
    
    user_profile = cursor.fetchone()
    if user_profile:
        city, city_normalized, city_display = user_profile
        print(f"   User city: {city}")
        print(f"   Normalized: {city_normalized}")
        print(f"   Display: {city_display}")
    else:
        print("   User profile not found!")
    
    # 4. Проверяем доступные боты в разных городах
    print(f"\n4. AVAILABLE BOTS IN DIFFERENT CITIES:")
    
    cities_to_check = ['Kyiv', 'Moscow', 'Saint Petersburg', 'Kharkiv']
    
    for city in cities_to_check:
        cursor.execute('''
            SELECT COUNT(*)
            FROM profiles p
            WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
            AND p.user_id != ?
            AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
            AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        ''', (city, today, user_id, user_id, user_id))
        
        available = cursor.fetchone()[0]
        print(f"   {city}: {available} bots available")
    
    # 5. Проверяем что происходит при смене города
    print(f"\n5. CITY SWITCH SIMULATION:")
    
    # Симулируем переход из Kyiv в Moscow
    from_city = 'Kyiv'
    to_city = 'Moscow'
    
    print(f"   Simulating switch: {from_city} -> {to_city}")
    
    # Проверяем ботов в исходном городе
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (from_city, today, user_id, user_id, user_id))
    
    from_city_bots = cursor.fetchone()[0]
    print(f"   Bots in {from_city}: {from_city_bots}")
    
    # Проверяем ботов в новом городе
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (to_city, today, user_id, user_id, user_id))
    
    to_city_bots = cursor.fetchone()[0]
    print(f"   Bots in {to_city}: {to_city_bots}")
    
    # 6. Проверяем SQL запросы которые могут вызывать зависание
    print(f"\n6. SQL QUERY PERFORMANCE CHECK:")
    
    import time
    
    # Тестируем get_profiles_for_swiping_exact_city
    start_time = time.time()
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
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
        LIMIT 10
    ''', (user_id, to_city, to_city, user_id, user_id, to_city))
    
    sql_results = cursor.fetchall()
    end_time = time.time()
    
    query_time = end_time - start_time
    print(f"   Query time: {query_time:.3f} seconds")
    print(f"   Results: {len(sql_results)} bots")
    
    if query_time > 2.0:
        print("   WARNING: Query is slow!")
    
    # 7. Проверяем есть ли проблемы с daily_bot_order
    print(f"\n7. DAILY_BOT_ORDER CHECK:")
    cursor.execute('''
        SELECT COUNT(*)
        FROM daily_bot_order dbo
        WHERE dbo.city_normalized = ? AND dbo.date = ?
    ''', (to_city, today))
    
    order_count = cursor.fetchone()[0]
    print(f"   Order entries for {to_city}: {order_count}")
    
    if order_count == 0:
        print(f"   WARNING: No daily order for {to_city}!")
    
    # 8. Проверяем возможные причины зависания
    print(f"\n8. POSSIBLE HANG CAUSES:")
    print("   1. FSM state not cleared properly")
    print("   2. Long SQL query execution")
    print("   3. Missing daily_bot_order for new city")
    print("   4. Profile views table lock")
    print("   5. Database connection issues")
    print("   6. Infinite loop in handlers")
    print("   7. Blocking I/O operation")
    
    # 9. Проверяем есть ли заблокированные записи
    print(f"\n9. DATABASE LOCK CHECK:")
    try:
        cursor.execute('PRAGMA lock_status')
        lock_status = cursor.fetchone()
        print(f"   Lock status: {lock_status}")
    except:
        print("   Cannot check lock status")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("CITY SWITCH HANG DEBUGGING COMPLETE!")
    print("\nRECOMMENDATIONS:")
    print("1. Clear FSM state when switching cities")
    print("2. Add timeout to SQL queries")
    print("3. Ensure daily_bot_order exists for all cities")
    print("4. Add logging to identify exact hang point")
    print("5. Check for infinite loops in handlers")

if __name__ == "__main__":
    debug_city_switch_hang()
