import sqlite3
from datetime import datetime

def test_daily_stability():
    """Тестируем стабильность порядка ботов в течение дня"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("TESTING DAILY STABILITY:")
    print("=" * 50)
    print(f"Date: {today}")
    print(f"City: {city_normalized}")
    
    # 1. Проверяем порядок в daily_bot_order
    print(f"\n1. DAILY ORDER IN TABLE:")
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = ?
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (city_normalized, today))
    
    table_order = cursor.fetchall()
    print(f"   First 10 bots in table order:")
    for i, bot in enumerate(table_order):
        user_id_bot, name, gender, order_index = bot
        print(f"     {order_index}. {name} ({gender})")
    
    # 2. Проверяем что вернет SQL запрос (как в боте)
    print(f"\n2. SQL QUERY RESULTS (as bot sees it):")
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
    
    sql_results = cursor.fetchall()
    print(f"   First 10 bots from SQL query:")
    for i, bot in enumerate(sql_results):
        user_id_bot, name, gender = bot
        print(f"     {i}. {name} ({gender})")
    
    # 3. Сравниваем порядок
    print(f"\n3. ORDER COMPARISON:")
    table_names = [bot[1] for bot in table_order]
    sql_names = [bot[1] for bot in sql_results]
    
    if table_names == sql_names:
        print("   OK ORDER MATCHES! Table order = SQL order")
    else:
        print("   ERROR ORDER MISMATCH!")
        print(f"   Table: {table_names[:5]}")
        print(f"   SQL:   {sql_names[:5]}")
    
    # 4. Проверяем стабильность - несколько запросов
    print(f"\n4. STABILITY TEST (multiple queries):")
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
    
    # Проверяем что все результаты одинаковы
    if all_results[0] == all_results[1] == all_results[2]:
        print("   OK STABLE! All queries return same order")
    else:
        print("   ERROR UNSTABLE! Queries return different orders")
    
    # 5. Проверяем количество активных ботов
    print(f"\n5. ACTIVE BOTS COUNT:")
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = DATE('now')
    ''', (city_normalized,))
    
    active_count = cursor.fetchone()[0]
    print(f"   Active bots in {city_normalized}: {active_count}")
    
    # 6. Проверяем gender balance
    cursor.execute('''
        SELECT p.gender, COUNT(*) 
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = DATE('now')
        GROUP BY p.gender
        ORDER BY p.gender
    ''', (city_normalized,))
    
    gender_balance = cursor.fetchall()
    print(f"\n6. GENDER BALANCE:")
    for gender, count in gender_balance:
        print(f"   {gender}: {count}")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("STABILITY TEST COMPLETE!")
    print("\nEXPECTED BEHAVIOR:")
    print("1. Same order throughout the day")
    print("2. Same bots for all users")
    print("3. Consistent gender balance")
    print("4. No random changes")

if __name__ == "__main__":
    test_daily_stability()
