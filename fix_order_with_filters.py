import sqlite3
from datetime import datetime

def fix_order_with_filters():
    """Исправляем порядок с учетом фильтров"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    city_normalized = 'Kyiv'
    user_id = 547486189
    
    print("FIXING ORDER WITH FILTERS:")
    print("=" * 50)
    
    # 1. Получаем ботов как их видит пользователь (с фильтрами)
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        WHERE p.user_id != ? 
        AND p.city_normalized = ?
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        AND p.user_id NOT IN (
            SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
        )
        AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
        ORDER BY p.user_id
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    available_bots = cursor.fetchall()
    print(f"Available bots for user {user_id}: {len(available_bots)}")
    
    # 2. Создаем порядок для доступных ботов
    cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city_normalized, today))
    
    for i, bot in enumerate(available_bots):
        bot_user_id, name, gender = bot
        cursor.execute('''
            INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
            VALUES (?, ?, ?, ?)
        ''', (city_normalized, bot_user_id, i, today))
    
    conn.commit()
    
    # 3. Проверяем результат
    print(f"\nAFTER FIXING:")
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = ? AND dbo.date = ?
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (city_normalized, today))
    
    order_results = cursor.fetchall()
    print(f"New order (first 10):")
    for bot in order_results:
        user_id_bot, name, gender, order_index = bot
        print(f"  {order_index}. {name} ({gender})")
    
    # 4. Тестируем SQL запрос
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
    print(f"\nSQL query results (first 10):")
    for i, bot in enumerate(sql_results):
        user_id_bot, name, gender = bot
        print(f"  {i}. {name} ({gender})")
    
    # 5. Сравниваем
    table_names = [bot[1] for bot in order_results]
    sql_names = [bot[1] for bot in sql_results]
    
    if table_names[:len(sql_names)] == sql_names:
        print(f"\nOK ORDER MATCHES! Table order = SQL order")
    else:
        print(f"\nERROR ORDER STILL MISMATCH!")
        print(f"Table: {table_names[:len(sql_names)]}")
        print(f"SQL:   {sql_names}")
    
    # 6. Проверяем стабильность
    print(f"\n6. STABILITY CHECK:")
    for i in range(3):
        cursor.execute('''
            SELECT p.name
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
        names = [bot[0] for bot in results]
        print(f"  Query {i+1}: {names}")
    
    conn.close()
    print(f"\nORDER FIXING COMPLETE!")

if __name__ == "__main__":
    fix_order_with_filters()
