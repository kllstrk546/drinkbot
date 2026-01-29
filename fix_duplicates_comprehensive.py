import sqlite3
import random

def fix_duplicates_comprehensive():
    """Исправляем все дубликаты за один проход"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("FIXING DUPLICATES COMPREHENSIVE:")
    print("=" * 50)
    
    # 1. Получаем все уникальные фото
    cursor.execute('''
        SELECT DISTINCT photo_id, bot_photo_path
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
    ''')
    
    all_unique_photos = cursor.fetchall()
    print(f"Available unique photos: {len(all_unique_photos)}")
    
    # 2. Получаем все ботов которые нужно исправить
    cursor.execute('''
        SELECT user_id, city_normalized, photo_id, bot_photo_path
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
        ORDER BY city_normalized, user_id
    ''')
    
    all_bots = cursor.fetchall()
    print(f"Total bots to check: {len(all_bots)}")
    
    # 3. Группируем ботов по городам
    city_bots = {}
    for bot in all_bots:
        user_id, city, photo_id, photo_path = bot
        if city not in city_bots:
            city_bots[city] = []
        city_bots[city].append(bot)
    
    # 4. Для каждого города создаем уникальные фото
    fixed_count = 0
    
    for city, bots in city_bots.items():
        print(f"\nProcessing {city}: {len(bots)} bots")
        
        # Находим дубликаты в этом городе
        photo_counts = {}
        for bot in bots:
            photo_id = bot[2]
            if photo_id not in photo_counts:
                photo_counts[photo_id] = []
            photo_counts[photo_id].append(bot)
        
        # Находим фото которые повторяются
        duplicates = {photo_id: bot_list for photo_id, bot_list in photo_counts.items() if len(bot_list) > 1}
        
        if duplicates:
            print(f"  Found {len(duplicates)} duplicate groups")
            
            # Собираем фото которые уже используются в городе
            used_photos = set()
            for bot in bots:
                used_photos.add(bot[2])
            
            # Находим доступные фото которые не используются в городе
            available_photos = []
            for photo_id, photo_path in all_unique_photos:
                if photo_id not in used_photos:
                    available_photos.append((photo_id, photo_path))
            
            # Перемешиваем доступные фото
            random.shuffle(available_photos)
            
            # Заменяем дубликаты
            photo_index = 0
            for duplicate_photo_id, duplicate_bots in duplicates.items():
                # Оставляем первого бота с этим фото
                keep_bot = duplicate_bots[0]
                replace_bots = duplicate_bots[1:]
                
                print(f"    Photo {duplicate_photo_id[:30]}...: keep {keep_bot[0]}, replace {len(replace_bots)}")
                
                for bot in replace_bots:
                    if photo_index < len(available_photos):
                        new_photo_id, new_photo_path = available_photos[photo_index]
                        
                        # Обновляем фото
                        cursor.execute('''
                            UPDATE profiles 
                            SET photo_id = ?, bot_photo_path = ?
                            WHERE user_id = ?
                        ''', (new_photo_id, new_photo_path, bot[0]))
                        
                        print(f"      Bot {bot[0]}: {duplicate_photo_id[:30]}... -> {new_photo_id[:30]}...")
                        fixed_count += 1
                        photo_index += 1
                    else:
                        print(f"      No more unique photos for bot {bot[0]}")
        else:
            print(f"  No duplicates found")
    
    conn.commit()
    
    # 5. Проверяем результат
    print(f"\nAFTER COMPREHENSIVE FIX:")
    cursor.execute('''
        SELECT city_normalized, photo_id, COUNT(*) as duplicate_count
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY city_normalized, photo_id
        HAVING duplicate_count > 1
        ORDER BY duplicate_count DESC
    ''')
    
    remaining_duplicates = cursor.fetchall()
    print(f"Remaining duplicates: {len(remaining_duplicates)}")
    
    if remaining_duplicates:
        print("Still problematic:")
        for city, photo_id, count in remaining_duplicates[:5]:
            print(f"  {city}: {photo_id[:30]}... ({count})")
    else:
        print("ALL DUPLICATES FIXED!")
    
    # 6. Проверяем Киев
    print(f"\nKYIV CHECK:")
    cursor.execute('''
        SELECT photo_id, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY photo_id
        HAVING count > 1
    ''')
    
    kyiv_duplicates = cursor.fetchall()
    if kyiv_duplicates:
        print(f"Kyiv still has {len(kyiv_duplicates)} duplicates")
    else:
        print("Kyiv: No duplicates!")
    
    # 7. Обновляем daily_bot_order
    print(f"\nUPDATING DAILY ORDER:")
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Пересоздаем порядок для всех городов
    cursor.execute('SELECT DISTINCT city_normalized FROM daily_bot_order WHERE date = ?', (today,))
    cities_with_order = [row[0] for row in cursor.fetchall()]
    
    for city in cities_with_order:
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city, today))
        
        cursor.execute('''
            SELECT user_id, name, gender
            FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
            ORDER BY RANDOM()
        ''', (city, today))
        
        city_active = cursor.fetchall()
        
        for i, bot in enumerate(city_active):
            user_id, name, gender = bot
            cursor.execute('''
                INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city, user_id, i, today))
        
        print(f"  {city}: {len(city_active)} bots")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print(f"COMPREHENSIVE DUPLICATE FIXING COMPLETE!")
    print(f"Fixed {fixed_count} bots")
    print(f"Remaining duplicates: {len(remaining_duplicates)}")

if __name__ == "__main__":
    fix_duplicates_comprehensive()
