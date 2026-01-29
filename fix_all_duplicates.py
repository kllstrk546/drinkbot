import sqlite3
import random

def fix_all_duplicates():
    """Исправляем все дубликаты фоток в городах"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("FIXING ALL PHOTO DUPLICATES:")
    print("=" * 50)
    
    # 1. Находим все дубликаты
    cursor.execute('''
        SELECT city_normalized, photo_id, COUNT(*) as duplicate_count,
               GROUP_CONCAT(user_id) as bot_ids
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY city_normalized, photo_id
        HAVING duplicate_count > 1
        ORDER BY duplicate_count DESC, city_normalized
    ''')
    
    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} duplicate groups")
    
    # 2. Для каждого дубликата заменяем фото у всех кроме одного
    fixed_count = 0
    
    for city, photo_id, duplicate_count, bot_ids_str in duplicates:
        print(f"\nFixing {city}: {photo_id[:30]}... ({duplicate_count} bots)")
        
        # Получаем ID ботов с этим фото
        bot_ids = [int(id_str) for id_str in bot_ids_str.split(',')]
        
        # Оставляем одного бота с этим фото, остальным меняем
        keep_bot_id = bot_ids[0]
        replace_bot_ids = bot_ids[1:]
        
        print(f"  Keeping: {keep_bot_id}")
        print(f"  Replacing: {replace_bot_ids}")
        
        # Получаем доступные фото для замены
        cursor.execute('''
            SELECT DISTINCT photo_id, bot_photo_path
            FROM profiles 
            WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
            AND photo_id != ?
            AND city_normalized = ?
        ''', (photo_id, city))
        
        available_photos = cursor.fetchall()
        
        if len(available_photos) >= len(replace_bot_ids):
            # Выбираем случайные фото для замены
            selected_photos = random.sample(available_photos, len(replace_bot_ids))
            
            for i, bot_id in enumerate(replace_bot_ids):
                new_photo_id, new_photo_path = selected_photos[i]
                
                # Обновляем фото
                cursor.execute('''
                    UPDATE profiles 
                    SET photo_id = ?, bot_photo_path = ?
                    WHERE user_id = ?
                ''', (new_photo_id, new_photo_path, bot_id))
                
                print(f"    Bot {bot_id}: {photo_id[:30]}... -> {new_photo_id[:30]}...")
                fixed_count += 1
        else:
            print(f"  Not enough unique photos in {city} (need {len(replace_bot_ids)}, have {len(available_photos)})")
            
            # Если не хватает фото, пробуем взять из других городов
            cursor.execute('''
                SELECT DISTINCT photo_id, bot_photo_path
                FROM profiles 
                WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
                AND photo_id != ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (photo_id, len(replace_bot_ids)))
            
            cross_city_photos = cursor.fetchall()
            
            if len(cross_city_photos) >= len(replace_bot_ids):
                for i, bot_id in enumerate(replace_bot_ids):
                    new_photo_id, new_photo_path = cross_city_photos[i]
                    
                    cursor.execute('''
                        UPDATE profiles 
                        SET photo_id = ?, bot_photo_path = ?
                        WHERE user_id = ?
                    ''', (new_photo_id, new_photo_path, bot_id))
                    
                    print(f"    Bot {bot_id}: {photo_id[:30]}... -> {new_photo_id[:30]}... (cross-city)")
                    fixed_count += 1
            else:
                print(f"  Cannot fix {city} - not enough photos available")
    
    conn.commit()
    
    # 3. Проверяем результат
    print(f"\nAFTER FIXING:")
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
        print("All duplicates fixed!")
    
    # 4. Проверяем Киев специально
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
        print(f"Kyiv still has {len(kyiv_duplicates)} duplicates:")
        for photo_id, count in kyiv_duplicates:
            print(f"  {photo_id[:30]}... ({count})")
    else:
        print("Kyiv: No duplicates!")
    
    # 5. Обновляем daily_bot_order после изменений
    print(f"\nUPDATING DAILY ORDER:")
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Пересоздаем порядок для Киева
    cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', ('Kyiv', today))
    
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND last_rotation_date = ?
        ORDER BY RANDOM()
    ''', (today,))
    
    kyiv_active = cursor.fetchall()
    
    for i, bot in enumerate(kyiv_active):
        user_id, name, gender = bot
        cursor.execute('''
            INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
            VALUES (?, ?, ?, ?)
        ''', ('Kyiv', user_id, i, today))
    
    print(f"Updated Kyiv order: {len(kyiv_active)} bots")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print(f"DUPLICATE FIXING COMPLETE!")
    print(f"Fixed {fixed_count} bots")
    print(f"Remaining duplicates: {len(remaining_duplicates)}")

if __name__ == "__main__":
    fix_all_duplicates()
