import sqlite3
from datetime import datetime

def fix_daily_stability():
    """Фиксируем порядок ботов на весь день"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("FIXING DAILY STABILITY:")
    print("=" * 50)
    
    # 1. Создаем временную таблицу для daily order
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_bot_order (
            city_normalized TEXT,
            bot_user_id INTEGER,
            order_index INTEGER,
            date TEXT,
            PRIMARY KEY (city_normalized, bot_user_id, date)
        )
    ''')
    
    # 2. Получаем все города с ботами
    cursor.execute('''
        SELECT DISTINCT city_normalized
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized IS NOT NULL AND city_normalized != ''
        ORDER BY city_normalized
    ''')
    
    cities = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(cities)} cities with bots")
    
    # 3. Для каждого города создаем фиксированный порядок
    for city in cities:
        print(f"\nProcessing {city}...")
        
        # Получаем активных ботов для города
        cursor.execute('''
            SELECT user_id, name, gender
            FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
            ORDER BY gender, user_id
        ''', (city, today))
        
        bots = cursor.fetchall()
        print(f"  Active bots: {len(bots)}")
        
        if not bots:
            continue
        
        # Удаляем старые записи для этого города и даты
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city, today))
        
        # Создаем фиксированный порядок
        for i, bot in enumerate(bots):
            user_id, name, gender = bot
            cursor.execute('''
                INSERT OR REPLACE INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city, user_id, i, today))
        
        print(f"  Created order for {len(bots)} bots")
    
    conn.commit()
    
    # 4. Проверяем результат для Киева
    print(f"\n4. KYIV DAILY ORDER CHECK:")
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = 'Kyiv' AND dbo.date = ?
        ORDER BY dbo.order_index
    ''', (today,))
    
    kyiv_order = cursor.fetchall()
    print(f"  Kyiv bots in order: {len(kyiv_order)}")
    
    for i, bot in enumerate(kyiv_order[:5]):
        user_id, name, gender, order_index = bot
        print(f"    {order_index}. {name} ({gender})")
    
    # 5. Создаем индекс для быстрого поиска
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_daily_bot_order_lookup 
        ON daily_bot_order (city_normalized, date, order_index)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("DAILY STABILITY FIX COMPLETE!")
    print("\nNEXT STEPS:")
    print("1. Update get_profiles_for_swiping_by_city_exact to use daily_bot_order")
    print("2. Remove ORDER BY RANDOM() from SQL queries")
    print("3. Use fixed order based on daily_bot_order table")

if __name__ == "__main__":
    fix_daily_stability()
