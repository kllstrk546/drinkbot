import sqlite3

def quick_gender_check():
    """Быстрая проверка гендера и фото"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("QUICK GENDER CHECK - MALE BOTS WITH FEMALE PHOTOS:")
    print("=" * 60)
    
    # Проверяем мужских ботов
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        AND photo_id IS NOT NULL AND photo_id != ""
        LIMIT 10
    ''', (city_normalized,))
    
    male_bots = cursor.fetchall()
    print(f"Male bots in Kyiv: {len(male_bots)}")
    
    # Проверяем женских ботов
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'female'
        AND photo_id IS NOT NULL AND photo_id != ""
        LIMIT 10
    ''', (city_normalized,))
    
    female_bots = cursor.fetchall()
    print(f"Female bots in Kyiv: {len(female_bots)}")
    
    # Проверяем откуда взялись фото
    print("\nChecking photo sources:")
    
    # Находим все фото и их гендеры
    cursor.execute('''
        SELECT gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        AND city_normalized != ?
        ORDER BY RANDOM()
        LIMIT 20
    ''', (city_normalized,))
    
    other_city_photos = cursor.fetchall()
    male_photos = [p for p in other_city_photos if p[0] == 'male']
    female_photos = [p for p in other_city_photos if p[0] == 'female']
    
    print(f"Available male photos from other cities: {len(male_photos)}")
    print(f"Available female photos from other cities: {len(female_photos)}")
    
    # Проверяем текущее распределение фото у киевских ботов
    print("\nCurrent photo assignment in Kyiv:")
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
    
    photo_assignment = cursor.fetchall()
    for bot_gender, photo_gender, count in photo_assignment:
        print(f"  {bot_gender} bots with {photo_gender} photos: {count}")
    
    # Показываем примеры проблемных ботов
    print("\nProblem examples (male bots with female photos):")
    cursor.execute('''
        SELECT p1.user_id, p1.name, p1.gender, p2.gender as photo_source_gender
        FROM profiles p1
        JOIN profiles p2 ON p1.photo_id = p2.photo_id
        WHERE p1.is_bot = 1 AND p1.city_normalized = ? 
        AND p1.gender = 'male' AND p2.gender = 'female'
        AND p1.photo_id IS NOT NULL AND p1.photo_id != ""
        LIMIT 5
    ''', (city_normalized,))
    
    problem_bots = cursor.fetchall()
    for bot in problem_bots:
        print(f"  {bot[1]} (male) has photo from {bot[3]} bot")
    
    conn.close()

if __name__ == "__main__":
    quick_gender_check()
