import sqlite3
from datetime import datetime

def debug_search_stability():
    """Диагностика стабильности поиска"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("DEBUGGING SEARCH STABILITY:")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"City: {city_normalized}")
    print(f"Date: {today}")
    
    # 1. Проверяем daily_bot_order
    print(f"\n1. DAILY_BOT_ORDER CHECK:")
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = ?
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (city_normalized, today))
    
    order_bots = cursor.fetchall()
    print(f"   Bots in daily order: {len(order_bots)}")
    for i, bot in enumerate(order_bots[:5]):
        user_id_bot, name, gender, order_index = bot
        print(f"     {order_index}. {name} ({gender})")
    
    # 2. Проверяем SQL запрос как в get_profiles_for_swiping_by_city_exact
    print(f"\n2. SQL QUERY (get_profiles_for_swiping_by_city_exact):")
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
    ''', (user_id, city_normalized, city_normalized, user_id, user_id, city_normalized))
    
    sql_bots = cursor.fetchall()
    print(f"   SQL query result: {len(sql_bots)}")
    for i, bot in enumerate(sql_bots[:5]):
        user_id_bot, name, gender = bot
        print(f"     {i}. {name} ({gender})")
    
    # 3. Сравниваем результаты
    print(f"\n3. COMPARISON:")
    order_names = [bot[1] for bot in order_bots[:len(sql_bots)]]
    sql_names = [bot[1] for bot in sql_bots]
    
    if order_names == sql_names:
        print("   OK: Daily order = SQL query")
    else:
        print("   ERROR: Daily order != SQL query")
        print(f"   Order: {order_names[:5]}")
        print(f"   SQL:   {sql_names[:5]}")
    
    # 4. Проверяем stability множественных запросов
    print(f"\n4. STABILITY TEST (multiple SQL queries):")
    all_results = []
    
    for i in range(3):
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
            LIMIT 5
        ''', (user_id, city_normalized, city_normalized, user_id, user_id, city_normalized))
        
        results = cursor.fetchall()
        names = [bot[1] for bot in results]
        all_results.append(names)
        print(f"   Query {i+1}: {names}")
    
    if all_results[0] == all_results[1] == all_results[2]:
        print("   OK: All SQL queries return same result")
    else:
        print("   ERROR: SQL queries return different results!")
    
    # 5. Проверяем profile_views (могут влиять)
    print(f"\n5. PROFILE_VIEWS CHECK:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    today_views = cursor.fetchone()[0]
    print(f"   Today's views: {today_views}")
    
    if today_views > 0:
        cursor.execute('''
            SELECT profile_id, view_date
            FROM profile_views 
            WHERE user_id = ? AND view_date = DATE('now')
            LIMIT 5
        ''', (user_id,))
        
        views = cursor.fetchall()
        print(f"   Recent views:")
        for profile_id, view_date in views:
            cursor.execute('SELECT name FROM profiles WHERE user_id = ?', (profile_id,))
            name = cursor.fetchone()[0]
            print(f"     {name} ({profile_id})")
    
    # 6. Проверяем likes
    print(f"\n6. LIKES CHECK:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM likes 
        WHERE from_user_id = ?
    ''', (user_id,))
    
    total_likes = cursor.fetchone()[0]
    print(f"   Total likes: {total_likes}")
    
    if total_likes > 0:
        cursor.execute('''
            SELECT to_user_id
            FROM likes 
            WHERE from_user_id = ?
            LIMIT 5
        ''', (user_id,))
        
        liked_ids = [row[0] for row in cursor.fetchall()]
        print(f"   Liked bots:")
        for liked_id in liked_ids:
            cursor.execute('SELECT name FROM profiles WHERE user_id = ?', (liked_id,))
            name = cursor.fetchone()[0]
            print(f"     {name} ({liked_id})")
    
    # 7. Проверяем что происходит с фильтрами
    print(f"\n7. USER FILTERS CHECK:")
    cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
    
    filters = cursor.fetchone()
    if filters:
        gender_filter, who_pays_filter = filters
        print(f"   Filters: gender={gender_filter}, who_pays={who_pays_filter}")
    
    # 8. Проверяем RANDOM() в других функциях
    print(f"\n8. OTHER FUNCTIONS CHECK:")
    
    # Проверяем find_profiles_for_swipe
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.user_id != ? AND p.city_normalized = ?
        AND dbo.city_normalized = ? AND dbo.date = DATE('now')
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        ORDER BY dbo.order_index
        LIMIT 5
    ''', (user_id, city_normalized, city_normalized, user_id))
    
    find_results = cursor.fetchall()
    find_names = [bot[1] for bot in find_results]
    print(f"   find_profiles_for_swipe: {find_names}")
    
    # 9. Проверяем есть ли разница в параметрах
    print(f"\n9. PARAMETER DIFFERENCES:")
    print(f"   User ID: {user_id}")
    print(f"   City: {city_normalized}")
    print(f"   Today: {today}")
    print(f"   DATE('now'): {datetime.now().strftime('%Y-%m-%d')}")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("DEBUGGING COMPLETE!")
    print("\nPOSSIBLE ISSUES:")
    print("1. FSM state not using SQL query")
    print("2. Different SQL functions being called")
    print("3. Profile_views affecting results")
    print("4. Date/time mismatch")
    print("5. Random order still being used somewhere")

if __name__ == "__main__":
    debug_search_stability()
