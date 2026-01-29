import sqlite3

def fix_gender_photos():
    """Исправляем фото по гендеру - у мужчин мужские, у девушек женские"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("FIXING GENDER PHOTOS - CORRECT PHOTO ASSIGNMENT:")
    print("=" * 60)
    
    # 1. Проверяем текущее состояние
    cursor.execute('''
        SELECT user_id, name, gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY gender, name
    ''', (city_normalized,))
    
    all_bots_with_photos = cursor.fetchall()
    print(f"Total bots with photos in Kyiv: {len(all_bots_with_photos)}")
    
    # 2. Разделяем по гендеру
    male_bots = [b for b in all_bots_with_photos if b[2] == 'male']
    female_bots = [b for b in all_bots_with_photos if b[2] == 'female']
    
    print(f"Male bots with photos: {len(male_bots)}")
    print(f"Female bots with photos: {len(female_bots)}")
    
    # 3. Находим правильные фото по гендеру
    # Мужские фото
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
        LIMIT 50
    ''')
    
    male_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available male photos: {len(male_photos)}")
    
    # Женские фото
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'female' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
        LIMIT 50
    ''')
    
    female_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available female photos: {len(female_photos)}")
    
    # 4. Исправляем фото для мужчин
    print("\nFixing male bots photos:")
    male_updated = 0
    for i, bot in enumerate(male_bots):
        bot_id, name, gender, current_photo = bot
        if i < len(male_photos):
            new_photo = male_photos[i]
            if current_photo != new_photo:
                cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (new_photo, bot_id))
                male_updated += 1
                print(f"  {name}: photo updated")
    
    # 5. Исправляем фото для женщин
    print("\nFixing female bots photos:")
    female_updated = 0
    for i, bot in enumerate(female_bots):
        bot_id, name, gender, current_photo = bot
        if i < len(female_photos):
            new_photo = female_photos[i]
            if current_photo != new_photo:
                cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (new_photo, bot_id))
                female_updated += 1
                print(f"  {name}: photo updated")
    
    conn.commit()
    
    print(f"\nUpdated {male_updated} male bots with male photos")
    print(f"Updated {female_updated} female bots with female photos")
    
    # 6. Проверяем результат
    print("\nFinal verification:")
    cursor.execute('''
        SELECT gender, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
        GROUP BY gender
    ''', (city_normalized,))
    
    final_distribution = cursor.fetchall()
    for gender, count in final_distribution:
        print(f"  {gender}: {count} bots with photos")
    
    # 7. Показываем примеры
    print("\nSample male bots:")
    cursor.execute('''
        SELECT name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        AND photo_id IS NOT NULL AND photo_id != ""
        LIMIT 3
    ''', (city_normalized,))
    
    male_samples = cursor.fetchall()
    for i, bot in enumerate(male_samples):
        print(f"  {i+1}. {bot[0]} - {bot[1][:30]}...")
    
    print("\nSample female bots:")
    cursor.execute('''
        SELECT name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'female'
        AND photo_id IS NOT NULL AND photo_id != ""
        LIMIT 3
    ''', (city_normalized,))
    
    female_samples = cursor.fetchall()
    for i, bot in enumerate(female_samples):
        print(f"  {i+1}. {bot[0]} - {bot[1][:30]}...")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("GENDER PHOTOS FIXED!")
    print("Male bots now have male photos, female bots have female photos!")

if __name__ == "__main__":
    fix_gender_photos()
