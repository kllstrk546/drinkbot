import sqlite3
from datetime import datetime

def focus_on_photos():
    """Фокус на фото - загружаем фото для ВСЕХ ботов в Киеве"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("FOCUS ON PHOTOS - UPLOADING FOR ALL KYIV BOTS:")
    print("=" * 60)
    
    # 1. Проверяем текущее состояние
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
    ''', (city_normalized,))
    
    total_bots = cursor.fetchone()[0]
    print(f"Total bots in Kyiv: {total_bots}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    bots_with_photos = cursor.fetchone()[0]
    print(f"Bots with photos: {bots_with_photos}")
    
    bots_without_photos = total_bots - bots_with_photos
    print(f"Bots without photos: {bots_without_photos}")
    
    # 2. Находим ботов без фото
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND (photo_id IS NULL OR photo_id = "")
        ORDER BY gender, name
    ''', (city_normalized,))
    
    bots_needing_photos = cursor.fetchall()
    print(f"Bots needing photos: {len(bots_needing_photos)}")
    
    # 3. Находим ВСЕ доступные фото из других городов
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        AND city_normalized != ?
        ORDER BY RANDOM()
    ''', (city_normalized,))
    
    available_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available photos from other cities: {len(available_photos)}")
    
    # 4. Распределяем фото
    updated_count = 0
    for i, bot in enumerate(bots_needing_photos):
        if i < len(available_photos):
            bot_id, name, gender = bot
            photo_id = available_photos[i]
            
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"  {i+1}. {name} ({gender}) - photo assigned")
        else:
            print(f"  {i+1}. {name} ({gender}) - NO PHOTO AVAILABLE")
    
    conn.commit()
    print(f"Updated {updated_count} bots with photos")
    
    # 5. Проверяем результат
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    final_photo_count = cursor.fetchone()[0]
    print(f"Final bots with photos: {final_photo_count}")
    
    # 6. Проверяем распределение по гендеру
    print("\nPhoto distribution by gender:")
    cursor.execute('''
        SELECT gender, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
        GROUP BY gender
    ''', (city_normalized,))
    
    gender_distribution = cursor.fetchall()
    for gender, count in gender_distribution:
        print(f"  {gender}: {count} bots with photos")
    
    # 7. Тестируем поиск для обоих пользователей
    print("\nTesting search for both users:")
    users = [547486189, 5483644714]
    
    for user_id in users:
        cursor.execute('''
            SELECT COUNT(*) FROM profiles 
            WHERE user_id != ? 
            AND city_normalized = ?
            AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
            AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
            AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        ''', (user_id, city_normalized, user_id, user_id, city_normalized))
        
        found_count = cursor.fetchone()[0]
        print(f"  User {user_id}: {found_count} profiles found")
    
    # 8. Показываем примеры ботов с фото
    print("\nSample bots with photos:")
    cursor.execute('''
        SELECT name, gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY gender, name
        LIMIT 5
    ''', (city_normalized,))
    
    sample_bots = cursor.fetchall()
    for i, bot in enumerate(sample_bots):
        print(f"  {i+1}. {bot[0]} ({bot[1]}) - {bot[2][:30]}...")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("PHOTO FOCUS COMPLETE!")
    print(f"All {final_photo_count} bots in Kyiv now have photos!")

if __name__ == "__main__":
    focus_on_photos()
