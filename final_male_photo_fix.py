import sqlite3

def final_male_photo_fix():
    """Финальное исправление - правильное распределение мужских фото"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("FINAL MALE PHOTO FIX - CORRECT DISTRIBUTION:")
    print("=" * 60)
    
    # 1. Получаем все уникальные мужские фото
    cursor.execute('''
        SELECT DISTINCT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
    ''')
    
    male_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available unique male photos: {len(male_photos)}")
    
    # 2. Получаем всех мужских ботов в Киеве
    cursor.execute('''
        SELECT user_id, name
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        ORDER BY name
    ''', (city_normalized,))
    
    male_bots = cursor.fetchall()
    print(f"Male bots in Kyiv: {len(male_bots)}")
    
    # 3. Распределяем мужские фото циклически
    updated_count = 0
    for i, bot in enumerate(male_bots):
        bot_id, bot_name = bot
        
        # Используем фото циклически
        photo_id = male_photos[i % len(male_photos)]
        
        cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
        updated_count += 1
        print(f"  {bot_name}: assigned male photo {i+1}/{len(male_photos)}")
    
    conn.commit()
    print(f"Updated {updated_count} male bots with correct male photos")
    
    # 4. Проверяем результат
    print("\nFinal verification:")
    cursor.execute('''
        SELECT p1.gender, p2.gender as photo_source_gender, COUNT(*) as count
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.city_normalized = ?
        AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        AND p2.is_bot = 1
        AND p1.gender = 'male'
        GROUP BY p1.gender, p2.gender
        ORDER BY p1.gender, p2.gender
    ''', (city_normalized,))
    
    final_assignment = cursor.fetchall()
    for bot_gender, photo_gender, count in final_assignment:
        status = "CORRECT" if bot_gender == photo_gender else "STILL WRONG"
        print(f"  {bot_gender} bots with {photo_gender} photos: {count} ({status})")
    
    # 5. Показываем примеры
    print("\nSample male bots with photos:")
    cursor.execute('''
        SELECT p1.name, p2.name as photo_source_name
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.city_normalized = ? AND p1.gender = 'male'
        AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        AND p2.is_bot = 1
        LIMIT 5
    ''', (city_normalized,))
    
    samples = cursor.fetchall()
    for i, sample in enumerate(samples):
        print(f"  {i+1}. {sample[0]} <- {sample[1]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("FINAL MALE PHOTO FIX COMPLETE!")
    print("All male bots should now have male photos!")

if __name__ == "__main__":
    final_male_photo_fix()
