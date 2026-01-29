import sqlite3

def deep_male_photo_analysis():
    """Глубокий анализ проблемы с мужскими фото"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("DEEP MALE PHOTO ANALYSIS:")
    print("=" * 80)
    
    # 1. Проверяем ВСЕ мужские фото в системе
    print("\n1. ALL MALE PHOTOS IN SYSTEM:")
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
        LIMIT 10
    ''')
    
    all_male_photos = cursor.fetchall()
    print(f"   Total male photos found: {len(all_male_photos)}")
    
    for i, photo in enumerate(all_male_photos[:5]):
        print(f"   {i+1}. {photo[1]} (ID: {photo[0]}) - {photo[2][:30]}...")
    
    # 2. Проверяем киевских мужских ботов
    print("\n2. KYIV MALE BOTS:")
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        ORDER BY name
    ''', (city_normalized,))
    
    kyiv_male_bots = cursor.fetchall()
    print(f"   Kyiv male bots: {len(kyiv_male_bots)}")
    
    for i, bot in enumerate(kyiv_male_bots):
        has_photo = "YES" if bot[2] else "NO"
        print(f"   {i+1}. {bot[1]} - Photo: {has_photo}")
        if bot[2]:
            print(f"       Photo ID: {bot[2][:30]}...")
    
    # 3. Проверяем источник фото для киевских мужских ботов
    print("\n3. PHOTO SOURCE ANALYSIS FOR KYIV MALE BOTS:")
    cursor.execute('''
        SELECT p1.user_id, p1.name, p1.gender, p2.gender as photo_source_gender, p2.name as photo_source_name
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.city_normalized = ? AND p1.gender = 'male'
        AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        AND p2.is_bot = 1
        ORDER BY p1.name
    ''', (city_normalized,))
    
    photo_sources = cursor.fetchall()
    print(f"   Photo sources for Kyiv male bots:")
    
    correct_count = 0
    wrong_count = 0
    
    for source in photo_sources:
        bot_name = source[1]
        bot_gender = source[2]
        photo_gender = source[3]
        photo_source_name = source[4]
        
        is_correct = bot_gender == photo_gender
        status = "CORRECT" if is_correct else "WRONG"
        
        if is_correct:
            correct_count += 1
        else:
            wrong_count += 1
        
        print(f"   {bot_name} ({bot_gender}) <- {photo_source_name} ({photo_gender}) [{status}]")
    
    print(f"\n   CORRECT assignments: {correct_count}")
    print(f"   WRONG assignments: {wrong_count}")
    
    # 4. Проверяем дубликаты фото
    print("\n4. PHOTO DUPLICATES CHECK:")
    cursor.execute('''
        SELECT photo_id, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        GROUP BY photo_id
        HAVING count > 1
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    duplicate_photos = cursor.fetchall()
    print(f"   Duplicate photos: {len(duplicate_photos)}")
    
    for dup in duplicate_photos:
        print(f"   Photo ID: {dup[0][:30]}... used {dup[1]} times")
    
    # 5. Проверяем распределение фото по городам
    print("\n5. PHOTO DISTRIBUTION BY CITIES:")
    cursor.execute('''
        SELECT p1.city_normalized, p1.gender, p2.gender as photo_source_gender, COUNT(*) as count
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        AND p2.is_bot = 1
        GROUP BY p1.city_normalized, p1.gender, p2.gender
        ORDER BY p1.city_normalized, p1.gender, p2.gender
    ''')
    
    city_distribution = cursor.fetchall()
    print("   City distribution:")
    for city, bot_gender, photo_gender, count in city_distribution:
        is_correct = bot_gender == photo_gender
        status = "OK" if is_correct else "WRONG"
        print(f"   {city}: {bot_gender} bots with {photo_gender} photos: {count} ({status})")
    
    # 6. Находим все уникальные мужские фото
    print("\n6. UNIQUE MALE PHOTOS:")
    cursor.execute('''
        SELECT DISTINCT photo_id, name
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
        LIMIT 10
    ''')
    
    unique_male_photos = cursor.fetchall()
    print(f"   Unique male photos: {len(unique_male_photos)}")
    
    for i, photo in enumerate(unique_male_photos):
        print(f"   {i+1}. {photo[1]} - {photo[0][:30]}...")
    
    # 7. Проверяем есть ли мужские фото вообще
    print("\n7. MALE PHOTOS EXISTENCE CHECK:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND gender = \'male\'')
    total_male_bots = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND gender = \'male\' AND photo_id IS NOT NULL AND photo_id != ""')
    male_bots_with_photos = cursor.fetchone()[0]
    
    print(f"   Total male bots in system: {total_male_bots}")
    print(f"   Male bots with photos: {male_bots_with_photos}")
    
    if male_bots_with_photos == 0:
        print("   !!! PROBLEM: NO MALE PHOTOS IN SYSTEM !!!")
    elif male_bots_with_photos < total_male_bots:
        print(f"   !!! PROBLEM: {total_male_bots - male_bots_with_photos} male bots without photos !!!")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")

if __name__ == "__main__":
    deep_male_photo_analysis()
