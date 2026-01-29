import sqlite3
from datetime import datetime

def create_filtered_daily_order():
    """Создаем порядок с учетом фильтров для каждого пользователя"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("CREATING FILTERED DAILY ORDER:")
    print("=" * 50)
    print(f"Date: {today}")
    
    # 1. Получаем все города
    cursor.execute('''
        SELECT DISTINCT city_normalized
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        ORDER BY city_normalized
    ''', (today,))
    
    cities = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(cities)} cities with active bots")
    
    # 2. Для каждого города создаем порядок
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
        
        # Создаем порядок для всех ботов (без фильтров)
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city, today))
        
        for i, bot in enumerate(active_bots):
            bot_user_id, name, gender = bot
            cursor.execute('''
                INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city, bot_user_id, i, today))
        
        print(f"  Created order for {len(active_bots)} bots")
    
    conn.commit()
    
    # 3. Тестируем для конкретного пользователя
    print(f"\nTESTING FOR USER 547486189 IN KYIV:")
    user_id = 547486189
    city = 'Kyiv'
    
    # Получаем порядок как видит пользователь
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        AND p.user_id NOT IN (
            SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
        )
        AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (city, today, user_id, user_id, user_id, city))
    
    user_results = cursor.fetchall()
    user_names = [f"{order_index}. {name} ({gender})" for user_id, name, gender, order_index in user_results]
    print(f"  User sees: {user_names[:5]}")
    
    # 4. Проверяем стабильность
    print(f"\n4. STABILITY TEST:")
    for i in range(3):
        cursor.execute('''
            SELECT p.name, p.gender
            FROM profiles p
            JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
            WHERE p.city_normalized = ? AND dbo.date = ?
            AND p.user_id != ?
            AND p.user_id NOT IN (
                SELECT to_user_id FROM likes WHERE from_user_id = ?
            )
            AND p.user_id NOT IN (
                SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
            )
            AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
            ORDER BY dbo.order_index
            LIMIT 5
        ''', (city, today, user_id, user_id, user_id, city))
        
        results = cursor.fetchall()
        names = [f"{name} ({gender})" for name, gender in results]
        print(f"  Query {i+1}: {names}")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("FILTERED DAILY ORDER CREATED!")
    print("\nKEY POINT:")
    print("1. Daily order created for all active bots")
    print("2. SQL query applies filters (likes, views)")
    print("3. ORDER BY daily_bot_order ensures stability")
    print("4. Same user sees same order on repeat searches")
    print("5. Different users may see different orders due to filters")

if __name__ == "__main__":
    create_filtered_daily_order()
