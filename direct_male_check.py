import sqlite3

def direct_male_check():
    """Прямая проверка мужских ботов"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("DIRECT MALE CHECK - NO JOINS:")
    print("=" * 50)
    
    # 1. Прямая проверка мужских ботов в Киеве
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY name
    ''', (city_normalized,))
    
    male_bots = cursor.fetchall()
    print(f"Male bots in Kyiv with photos: {len(male_bots)}")
    
    # 2. Проверяем каждый бот индивидуально
    correct_count = 0
    wrong_count = 0
    
    for bot in male_bots:
        bot_id, bot_name, photo_id = bot
        
        # Ищем источник фото
        cursor.execute('''
            SELECT gender, name
            FROM profiles 
            WHERE photo_id = ? AND is_bot = 1
            LIMIT 1
        ''', (photo_id,))
        
        source = cursor.fetchone()
        
        if source:
            source_gender, source_name = source
            
            if source_gender == 'male':
                correct_count += 1
                print(f"  CORRECT: {bot_name} <- {source_name} ({source_gender})")
            else:
                wrong_count += 1
                print(f"  WRONG: {bot_name} <- {source_name} ({source_gender})")
        else:
            print(f"  UNKNOWN: {bot_name} <- Source not found")
    
    print(f"\nSummary:")
    print(f"  Correct assignments: {correct_count}")
    print(f"  Wrong assignments: {wrong_count}")
    
    # 3. Проверяем сколько всего мужских фото в системе
    cursor.execute('''
        SELECT COUNT(DISTINCT photo_id)
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''')
    
    unique_male_photos = cursor.fetchone()[0]
    print(f"  Unique male photos in system: {unique_male_photos}")
    
    conn.close()

if __name__ == "__main__":
    direct_male_check()
