import sqlite3
from datetime import datetime
import random

def activate_remaining_bots():
    """Активация всех оставшихся ботов"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("ACTIVATING REMAINING BOTS:")
    print("=" * 50)
    
    # 1. Проверяем сколько ботов неактивны
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1
    ''')
    total_bots = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?
    ''', (today,))
    active_today = cursor.fetchone()[0]
    
    inactive_bots = total_bots - active_today
    print(f"Total bots: {total_bots}")
    print(f"Active today: {active_today}")
    print(f"Inactive bots: {inactive_bots}")
    
    # 2. Активируем ВСЕХ ботов на сегодня
    print(f"\n2. ACTIVATING ALL INACTIVE BOTS:")
    
    cursor.execute('''
        UPDATE profiles 
        SET last_rotation_date = ?
        WHERE is_bot = 1 AND last_rotation_date IS NULL OR last_rotation_date != ?
    ''', (today, today))
    
    activated_count = cursor.rowcount
    print(f"Activated {activated_count} bots")
    
    # 3. Проверяем сколько теперь активно
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?
    ''', (today,))
    new_active_count = cursor.fetchone()[0]
    print(f"Total active today: {new_active_count}")
    
    # 4. Создаем новый daily_bot_order
    print(f"\n3. CREATING NEW DAILY_BOT_ORDER:")
    
    # Удаляем старые записи
    cursor.execute('DELETE FROM daily_bot_order WHERE date = ?', (today,))
    
    # Получаем всех активных ботов
    cursor.execute('''
        SELECT user_id, city_normalized, gender, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        ORDER BY city_normalized, gender, user_id
    ''', (today,))
    
    all_bots = cursor.fetchall()
    print(f"Found {len(all_bots)} active bots")
    
    # Проверяем наличие фотографий
    bots_with_photos = 0
    bots_without_photos = 0
    
    city_bots = {}
    for user_id, city, gender, name, photo_id in all_bots:
        if city not in city_bots:
            city_bots[city] = {"male": [], "female": []}
        
        city_bots[city][gender].append(user_id)
        
        if photo_id:
            bots_with_photos += 1
        else:
            bots_without_photos += 1
    
    print(f"Bots with photos: {bots_with_photos}")
    print(f"Bots without photos: {bots_without_photos}")
    
    # Создаем порядок для каждого города
    total_order_entries = 0
    for city, bot_lists in city_bots.items():
        all_city_bots = []
        
        # Добавляем мужчин
        for bot_id in bot_lists.get("male", []):
            all_city_bots.append(bot_id)
        
        # Добавляем женщин
        for bot_id in bot_lists.get("female", []):
            all_city_bots.append(bot_id)
        
        # Перемешиваем для разнообразия
        random.shuffle(all_city_bots)
        
        # Создаем записи в daily_bot_order
        for order_index, bot_id in enumerate(all_city_bots):
            cursor.execute('''
                INSERT INTO daily_bot_order (bot_user_id, city_normalized, date, order_index)
                VALUES (?, ?, ?, ?)
            ''', (bot_id, city, today, order_index))
            total_order_entries += 1
    
    print(f"Created {total_order_entries} daily order entries")
    
    # 5. Топ города
    print(f"\n4. TOP CITIES:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 15
    ''', (today,))
    
    top_cities = cursor.fetchall()
    for city, count in top_cities:
        print(f"  {city}: {count} bots")
    
    # 6. Гендерное распределение
    print(f"\n5. GENDER DISTRIBUTION:")
    cursor.execute('''
        SELECT gender, COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY gender
    ''', (today,))
    
    gender_dist = cursor.fetchall()
    for gender, count in gender_dist:
        print(f"  {gender}: {count} bots")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("REMAINING BOTS ACTIVATION COMPLETE!")
    print(f"\nFINAL STATUS:")
    print(f"Total bots in database: {total_bots}")
    print(f"Active today: {new_active_count}")
    print(f"Daily order entries: {total_order_entries}")
    print(f"Cities with bots: {len(city_bots)}")
    print(f"Bots with photos: {bots_with_photos}")
    
    if bots_without_photos > 0:
        print(f"WARNING: {bots_without_photos} bots without photos!")
    
    print(f"\nALL BOTS READY! 🚀")

if __name__ == "__main__":
    activate_remaining_bots()
