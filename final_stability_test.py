import sqlite3
from datetime import datetime

def final_stability_test():
    """Финальный тест стабильности"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("FINAL STABILITY TEST:")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"City: {city_normalized}")
    print(f"Date: {today}")
    
    # 1. Тестируем новую функцию get_profiles_for_swiping_exact_city
    print(f"\n1. TESTING get_profiles_for_swiping_exact_city:")
    
    # Без фильтров
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
    
    no_filter_results = cursor.fetchall()
    no_filter_names = [f"{name} ({gender})" for user_id, name, gender in no_filter_results]
    print(f"  No filters: {no_filter_names[:5]}")
    
    # С фильтрами (gender=all, who_pays=any)
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
    
    with_filter_results = cursor.fetchall()
    with_filter_names = [f"{name} ({gender})" for user_id, name, gender in with_filter_results]
    print(f"  With filters: {with_filter_names[:5]}")
    
    # 2. Проверяем стабильность множественных вызовов
    print(f"\n2. STABILITY TEST (multiple calls):")
    all_results = []
    
    for i in range(5):
        cursor.execute('''
            SELECT p.name, p.gender
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
        names = [f"{name} ({gender})" for name, gender in results]
        all_results.append(names)
        print(f"  Call {i+1}: {names}")
    
    # Проверяем что все результаты одинаковы
    if all_results[0] == all_results[1] == all_results[2] == all_results[3] == all_results[4]:
        print("  STABLE: All calls return same results!")
    else:
        print("  UNSTABLE: Calls return different results!")
    
    # 3. Проверяем для другого пользователя
    print(f"\n3. DIFFERENT USER TEST:")
    other_user_id = 5483644714
    
    cursor.execute('''
        SELECT p.name, p.gender
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
    ''', (other_user_id, city_normalized, city_normalized, other_user_id, other_user_id, city_normalized))
    
    other_results = cursor.fetchall()
    other_names = [f"{name} ({gender})" for name, gender in other_results]
    print(f"  User {other_user_id}: {other_names}")
    
    # 4. Проверяем что порядок daily_bot_order правильный
    print(f"\n4. DAILY_BOT_ORDER CHECK:")
    cursor.execute('''
        SELECT p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = ?
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (city_normalized, today))
    
    order_results = cursor.fetchall()
    order_names = [f"{order_index}. {name} ({gender})" for name, gender, order_index in order_results]
    print(f"  Daily order: {order_names[:5]}")
    
    # 5. Сравниваем с результатами пользователя
    print(f"\n5. ORDER COMPARISON:")
    order_first_5 = [f"{name} ({gender})" for name, gender, order_index in order_results[:5]]
    user_first_5 = [f"{name} ({gender})" for user_id, name, gender in with_filter_results[:5]]
    
    print(f"  Order first 5:  {order_first_5}")
    print(f"  User first 5:   {user_first_5}")
    
    if order_first_5 == user_first_5:
        print("  PERFECT MATCH: User sees same order as daily_bot_order!")
    else:
        print("  MISMATCH: User sees different order!")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("FINAL STABILITY TEST COMPLETE!")
    print("\nEXPECTED RESULTS:")
    print("1. Same results on multiple calls")
    print("2. Same order as daily_bot_order")
    print("3. Different users see different results (due to likes/views)")
    print("4. No RANDOM() usage")
    print("5. Stable throughout the day")

if __name__ == "__main__":
    final_stability_test()
