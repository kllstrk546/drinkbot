import sqlite3
from datetime import datetime

def fix_order_mismatch():
    """Исправляем порядок - создаем order только для активных ботов"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    city_normalized = 'Kyiv'
    
    print("FIXING ORDER MISMATCH:")
    print("=" * 50)
    
    # 1. Получаем всех активных ботов в Киеве
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
        ORDER BY gender, user_id
    ''', (city_normalized, today))
    
    active_bots = cursor.fetchall()
    print(f"Active bots in {city_normalized}: {len(active_bots)}")
    
    # 2. Перемешиваем для разнообразия
    import random
    random.shuffle(active_bots)
    
    # 3. Удаляем старые записи порядка
    cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city_normalized, today))
    
    # 4. Создаем новый порядок только для активных ботов
    for i, bot in enumerate(active_bots):
        user_id, name, gender = bot
        cursor.execute('''
            INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
            VALUES (?, ?, ?, ?)
        ''', (city_normalized, user_id, i, today))
    
    conn.commit()
    
    # 5. Проверяем результат
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
        user_id, name, gender, order_index = bot
        print(f"  {order_index}. {name} ({gender})")
    
    # 6. Тестируем SQL запрос
    user_id = 547486189
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
    
    # 7. Сравниваем
    table_names = [bot[1] for bot in order_results]
    sql_names = [bot[1] for bot in sql_results]
    
    if table_names[:len(sql_names)] == sql_names:
        print(f"\nOK ORDER MATCHES! Table order = SQL order")
    else:
        print(f"\nERROR ORDER STILL MISMATCH!")
        print(f"Table: {table_names[:len(sql_names)]}")
        print(f"SQL:   {sql_names}")
    
    conn.close()
    print(f"\nORDER FIXING COMPLETE!")

if __name__ == "__main__":
    fix_order_mismatch()
