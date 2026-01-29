import sqlite3

def emergency_photo_fix():
    """Экстренное исправление - правильные фото по гендеру"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("EMERGENCY PHOTO FIX - CORRECT GENDER PHOTOS:")
    print("=" * 60)
    
    # 1. Находим ВСЕ мужские фото в системе
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
    ''')
    
    all_male_photos = [row[0] for row in cursor.fetchall()]
    print(f"Total male photos in system: {len(all_male_photos)}")
    
    # 2. Находим ВСЕ женские фото в системе
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'female' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
    ''')
    
    all_female_photos = [row[0] for row in cursor.fetchall()]
    print(f"Total female photos in system: {len(all_female_photos)}")
    
    # 3. Получаем киевских ботов
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
    ''', (city_normalized,))
    
    kyiv_bots = cursor.fetchall()
    male_bots = [b for b in kyiv_bots if b[2] == 'male']
    female_bots = [b for b in kyiv_bots if b[2] == 'female']
    
    print(f"Kyiv male bots: {len(male_bots)}")
    print(f"Kyiv female bots: {len(female_bots)}")
    
    # 4. Распределяем правильные фото
    updated_count = 0
    
    # Мужские боты получают мужские фото
    print("\nAssigning male photos to male bots:")
    for i, bot in enumerate(male_bots):
        bot_id, name, gender = bot
        if i < len(all_male_photos):
            photo_id = all_male_photos[i % len(all_male_photos)]  # Циклически
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"  {name} (male) -> male photo")
    
    # Женские боты получают женские фото
    print("\nAssigning female photos to female bots:")
    for i, bot in enumerate(female_bots):
        bot_id, name, gender = bot
        if i < len(all_female_photos):
            photo_id = all_female_photos[i % len(all_female_photos)]  # Циклически
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"  {name} (female) -> female photo")
    
    conn.commit()
    print(f"\nUpdated {updated_count} bots with correct gender photos")
    
    # 5. Проверяем результат
    print("\nVerification:")
    cursor.execute('''
        SELECT p1.gender, p2.gender as photo_source_gender, COUNT(*) as count
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.city_normalized = ?
        AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        AND p2.is_bot = 1
        GROUP BY p1.gender, p2.gender
        ORDER BY p1.gender, p2.gender
    ''', (city_normalized,))
    
    final_assignment = cursor.fetchall()
    for bot_gender, photo_gender, count in final_assignment:
        status = "✅ CORRECT" if bot_gender == photo_gender else "❌ WRONG"
        print(f"  {bot_gender} bots with {photo_gender} photos: {count} {status}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("EMERGENCY FIX COMPLETE!")
    print("Now male bots have male photos, female bots have female photos!")

if __name__ == "__main__":
    emergency_photo_fix()
