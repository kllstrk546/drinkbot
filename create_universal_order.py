import sqlite3
from datetime import datetime

def create_universal_order():
    """Создаем универсальный порядок для всех пользователей"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("CREATING UNIVERSAL ORDER:")
    print("=" * 50)
    print(f"Date: {today}")
    
    # 1. Получаем все города с активными ботами
    cursor.execute('''
        SELECT DISTINCT city_normalized
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        ORDER BY city_normalized
    ''', (today,))
    
    cities = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(cities)} cities with active bots")
    
    # 2. Для каждого города создаем универсальный порядок
    for city in cities:
        print(f"\nProcessing {city}...")
        
        # Получаем всех активных ботов в городе
        cursor.execute('''
            SELECT user_id, name, gender
            FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
            ORDER BY gender, user_id
        ''', (city, today))
        
        active_bots = cursor.fetchall()
        print(f"  Active bots: {len(active_bots)}")
        
        if not active_bots:
            continue
        
        # Удаляем старые записи порядка
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city, today))
        
        # Создаем универсальный порядок (без фильтров)
        for i, bot in enumerate(active_bots):
            bot_user_id, name, gender = bot
            cursor.execute('''
                INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city, bot_user_id, i, today))
        
        print(f"  Created order for {len(active_bots)} bots")
    
    conn.commit()
    
    # 3. Проверяем результат
    print(f"\nUNIVERSAL ORDER CREATED:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as bots_in_order
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized
        ORDER BY bots_in_order DESC
        LIMIT 10
    ''', (today,))
    
    order_cities = cursor.fetchall()
    print("Top 10 cities by order size:")
    for city, count in order_cities:
        print(f"  {city}: {count} bots")
    
    # 4. Тестируем для разных пользователей
    print(f"\nTESTING FOR DIFFERENT USERS:")
    test_users = [547486189, 5483644714]
    
    for user_id in test_users:
        print(f"\nUser {user_id}:")
        
        # Количество доступных ботов в Киеве
        cursor.execute('''
            SELECT COUNT(*)
            FROM profiles p
            JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
            WHERE p.city_normalized = 'Kyiv' AND dbo.date = DATE('now')
            AND p.user_id != ?
            AND p.user_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            AND p.user_id NOT IN (
                SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
            )
            AND (p.is_bot = 0 OR (p.city_normalized = 'Kyiv' AND p.last_rotation_date = DATE('now')))
        ''', (user_id, user_id, user_id))
        
        available_count = cursor.fetchone()[0]
        print(f"  Available bots in Kyiv: {available_count}")
        
        # Первые 5 ботов
        cursor.execute('''
            SELECT p.name, p.gender
            FROM profiles p
            JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
            WHERE p.city_normalized = 'Kyiv' AND dbo.date = DATE('now')
            AND p.user_id != ?
            AND p.user_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            AND p.user_id NOT IN (
                SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
            )
            AND (p.is_bot = 0 OR (p.city_normalized = 'Kyiv' AND p.last_rotation_date = DATE('now')))
            ORDER BY dbo.order_index
            LIMIT 5
        ''', (user_id, user_id, user_id))
        
        first_bots = cursor.fetchall()
        bot_names = [f"{name} ({gender})" for name, gender in first_bots]
        print(f"  First 5 bots: {bot_names}")
    
    # 5. Проверяем стабильность для одного пользователя
    print(f"\nSTABILITY TEST FOR USER 547486189:")
    for i in range(3):
        cursor.execute('''
            SELECT p.name
            FROM profiles p
            JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
            WHERE p.city_normalized = 'Kyiv' AND dbo.date = DATE('now')
            AND p.user_id != ?
            AND p.user_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            AND p.user_id NOT IN (
                SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
            )
            AND (p.is_bot = 0 OR (p.city_normalized = 'Kyiv' AND p.last_rotation_date = DATE('now')))
            ORDER BY dbo.order_index
            LIMIT 5
        ''', (547486189, 547486189, 547486189))
        
        results = cursor.fetchall()
        names = [bot[0] for bot in results]
        print(f"  Query {i+1}: {names}")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("UNIVERSAL ORDER CREATION COMPLETE!")
    print("\nKEY FEATURES:")
    print("1. Single order for all users in each city")
    print("2. Filters applied in SQL, not in order creation")
    print("3. Same base order for everyone")
    print("4. Different results based on user's likes/views")
    print("\nTO TEST:")
    print("1. Different users should see different bots")
    print("2. Same user should see same bots on repeat searches")
    print("3. Order should be stable throughout the day")

if __name__ == "__main__":
    create_universal_order()
