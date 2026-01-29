import sqlite3
from datetime import datetime

def debug_bot_handlers():
    """Диагностика что происходит в handlers"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("DEBUGGING BOT HANDLERS:")
    print("=" * 60)
    
    # 1. Проверяем все функции которые могут использоваться
    print(f"\n1. TESTING ALL SQL FUNCTIONS:")
    
    # get_profiles_for_swiping_by_city_exact
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
    
    exact_results = cursor.fetchall()
    exact_names = [f"{name} ({gender})" for user_id, name, gender in exact_results]
    print(f"  get_profiles_for_swiping_by_city_exact: {exact_names[:5]}")
    
    # find_profiles_for_swipe
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
        LIMIT 10
    ''', (user_id, city_normalized, city_normalized, user_id))
    
    find_results = cursor.fetchall()
    find_names = [f"{name} ({gender})" for user_id, name, gender in find_results]
    print(f"  find_profiles_for_swipe: {find_names[:5]}")
    
    # get_profiles_for_swiping_nearby_by_city
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.user_id != ? AND p.city_normalized = ?
        AND dbo.city_normalized IN (?) AND dbo.date = DATE('now')
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (user_id, city_normalized, city_normalized, user_id))
    
    nearby_results = cursor.fetchall()
    nearby_names = [f"{name} ({gender})" for user_id, name, gender in nearby_results]
    print(f"  get_profiles_for_swiping_nearby_by_city: {nearby_names[:5]}")
    
    # get_profiles_for_swiping_with_filters
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.user_id != ? AND p.city_normalized = ?
        AND dbo.city_normalized = p.city_normalized
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
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    filters_results = cursor.fetchall()
    filters_names = [f"{name} ({gender})" for user_id, name, gender in filters_results]
    print(f"  get_profiles_for_swiping_with_filters: {filters_names[:5]}")
    
    # 2. Проверяем есть ли разница
    print(f"\n2. COMPARING FUNCTIONS:")
    print(f"  exact:  {exact_names[:3]}")
    print(f"  find:   {find_names[:3]}")
    print(f"  nearby: {nearby_names[:3]}")
    print(f"  filters: {filters_names[:3]}")
    
    # 3. Проверяем что может вызывать RANDOM()
    print(f"\n3. CHECKING FOR RANDOM() USAGE:")
    
    # Ищем функции которые все еще используют RANDOM()
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        WHERE p.user_id != ? AND p.city_normalized = ?
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        ORDER BY RANDOM()
        LIMIT 5
    ''', (user_id, city_normalized, user_id))
    
    random_results = cursor.fetchall()
    random_names = [f"{name} ({gender})" for user_id, name, gender in random_results]
    print(f"  RANDOM() query: {random_names}")
    
    # 4. Проверяем profile_views state
    print(f"\n4. PROFILE_VIEWS STATE:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    today_views = cursor.fetchone()[0]
    print(f"  Today's views: {today_views}")
    
    if today_views > 0:
        cursor.execute('''
            SELECT profile_id, view_date
            FROM profile_views 
            WHERE user_id = ? AND view_date = DATE('now')
            ORDER BY view_date DESC
            LIMIT 5
        ''', (user_id,))
        
        views = cursor.fetchall()
        print(f"  Recent views:")
        for profile_id, view_date in views:
            cursor.execute('SELECT name FROM profiles WHERE user_id = ?', (profile_id,))
            name = cursor.fetchone()[0]
            print(f"    {name} ({profile_id})")
    
    # 5. Проверяем есть ли проблема в handlers/start.py
    print(f"\n5. HANDLERS INVESTIGATION:")
    print("  Possible issues:")
    print("  1. FSM state storing profiles list")
    print("  2. Different function being called")
    print("  3. Manual filtering after SQL query")
    print("  4. Cache issues")
    print("  5. Multiple search paths")
    
    # 6. Симуляция проблемы
    print(f"\n6. PROBLEM SIMULATION:")
    print("  If user sees different bots on new search:")
    print("  - FSM state might be cleared")
    print("  - New SQL query executed")
    print("  - But daily_bot_order should ensure same results")
    print("  - Unless profile_views are affecting results")
    
    # 7. Проверяем стабильность с очисткой views
    print(f"\n7. STABILITY WITHOUT VIEWS:")
    
    # Временно очищаем views для теста
    cursor.execute('''
        CREATE TEMPORARY TABLE temp_views AS
        SELECT * FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    cursor.execute('''
        DELETE FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    # Тестируем без views
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = 'Kyiv' AND dbo.date = DATE('now')
        AND p.user_id != ?
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        ORDER BY dbo.order_index
        LIMIT 5
    ''', (user_id, user_id))
    
    no_views_results = cursor.fetchall()
    no_views_names = [f"{name} ({gender})" for user_id, name, gender in no_views_results]
    print(f"  Without views: {no_views_names}")
    
    # Восстанавливаем views
    cursor.execute('''
        INSERT INTO profile_views 
        SELECT * FROM temp_views
    ''')
    
    cursor.execute('DROP TABLE temp_views')
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("HANDLERS DEBUGGING COMPLETE!")
    print("\nMOST LIKELY ISSUES:")
    print("1. FSM state cleared on new search")
    print("2. New profiles list generated")
    print("3. But daily_bot_order should ensure consistency")
    print("4. Check if bot code is using updated functions")

if __name__ == "__main__":
    debug_bot_handlers()
