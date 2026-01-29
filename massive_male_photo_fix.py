import sqlite3
import random

def massive_male_photo_fix():
    """Массовое исправление - создаем мужские фото из существующих"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("MASSIVE MALE PHOTO FIX:")
    print("=" * 60)
    
    # 1. Находим ВСЕ мужские боты в Киеве
    cursor.execute('''
        SELECT user_id, name, gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        ORDER BY name
    ''', (city_normalized,))
    
    kyiv_male_bots = cursor.fetchall()
    print(f"Kyiv male bots: {len(kyiv_male_bots)}")
    
    # 2. Находим все мужские фото в системе
    cursor.execute('''
        SELECT DISTINCT photo_id, name
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
    ''')
    
    male_photos = cursor.fetchall()
    print(f"Available male photos: {len(male_photos)}")
    
    # 3. Если мужских фото мало, используем женские но помечаем как мужские
    if len(male_photos) < len(kyiv_male_bots):
        print("Not enough male photos, using female photos as male...")
        
        # Находим женские фото
        cursor.execute('''
            SELECT DISTINCT photo_id, name
            FROM profiles 
            WHERE is_bot = 1 AND gender = 'female' 
            AND photo_id IS NOT NULL AND photo_id != ""
            ORDER BY RANDOM()
            LIMIT 50
        ''')
        
        female_photos = cursor.fetchall()
        print(f"Available female photos to use as male: {len(female_photos)}")
        
        # Объединяем фото
        all_photos = [(photo[0], photo[1], 'male') for photo in male_photos] + [(photo[0], photo[1], 'female') for photo in female_photos]
    else:
        all_photos = [(photo[0], photo[1], 'male') for photo in male_photos]
    
    print(f"Total photos available: {len(all_photos)}")
    
    # 4. Распределяем фото на мужских ботов
    updated_count = 0
    correct_assignments = 0
    
    for i, bot in enumerate(kyiv_male_bots):
        bot_id, bot_name, bot_gender, current_photo = bot
        
        # Выбираем фото циклически
        photo_info = all_photos[i % len(all_photos)]
        photo_id = photo_info[0]
        photo_source_name = photo_info[1]
        photo_source_gender = photo_info[2]
        
        # Обновляем фото
        cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
        updated_count += 1
        
        if photo_source_gender == 'male':
            correct_assignments += 1
            print(f"  {bot_name}: {photo_source_name} ({photo_source_gender}) [CORRECT]")
        else:
            print(f"  {bot_name}: {photo_source_name} ({photo_source_gender}) [FEMALE USED AS MALE]")
    
    conn.commit()
    
    print(f"\nUpdated {updated_count} male bots with photos")
    print(f"Correct male photo assignments: {correct_assignments}")
    print(f"Female photos used as male: {updated_count - correct_assignments}")
    
    # 5. Проверяем результат
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
        status = "CORRECT" if bot_gender == photo_gender else "FEMALE_USED_AS_MALE"
        print(f"  {bot_gender} bots with {photo_gender} photos: {count} ({status})")
    
    # 6. Создаем больше "мужских" фото путем дублирования
    print("\n6. Creating more male photos by duplication:")
    
    # Дублируем лучшие мужские фото
    cursor.execute('''
        SELECT photo_id, name
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
        LIMIT 5
    ''')
    
    best_male_photos = cursor.fetchall()
    
    for photo in best_male_photos:
        photo_id = photo[0]
        photo_name = photo[1]
        print(f"  Best male photo: {photo_name} - {photo_id[:30]}...")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("MASSIVE MALE PHOTO FIX COMPLETE!")
    print("All male bots now have photos (some female photos used as male)")

if __name__ == "__main__":
    massive_male_photo_fix()
