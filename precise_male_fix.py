import sqlite3

def precise_male_fix():
    """Точное исправление - каждое фото индивидуально"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    
    print("PRECISE MALE FIX - INDIVIDUAL ASSIGNMENT:")
    print("=" * 60)
    
    # 1. Получаем все мужские фото
    cursor.execute('''
        SELECT DISTINCT photo_id, name
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'male' 
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY RANDOM()
    ''')
    
    male_photos = cursor.fetchall()
    print(f"Available male photos: {len(male_photos)}")
    
    # 2. Получаем всех мужских ботов в Киеве
    cursor.execute('''
        SELECT user_id, name
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        ORDER BY name
    ''', (city_normalized,))
    
    male_bots = cursor.fetchall()
    print(f"Male bots in Kyiv: {len(male_bots)}")
    
    # 3. Назначаем правильные фото
    updated_count = 0
    for i, bot in enumerate(male_bots):
        bot_id, bot_name = bot
        
        # Берем фото циклически
        photo_info = male_photos[i % len(male_photos)]
        photo_id = photo_info[0]
        photo_name = photo_info[1]
        
        # Обновляем
        cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
        updated_count += 1
        
        print(f"  {bot_name} <- {photo_name} (male photo)")
    
    conn.commit()
    print(f"Updated {updated_count} male bots")
    
    # 4. Проверяем результат
    print("\nVerification:")
    cursor.execute('''
        SELECT user_id, name, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        AND photo_id IS NOT NULL AND photo_id != ""
        ORDER BY name
    ''', (city_normalized,))
    
    final_bots = cursor.fetchall()
    correct_count = 0
    
    for bot in final_bots:
        bot_id, bot_name, photo_id = bot
        
        # Проверяем источник
        cursor.execute('''
            SELECT gender, name
            FROM profiles 
            WHERE photo_id = ? AND is_bot = 1 AND gender = 'male'
            LIMIT 1
        ''', (photo_id,))
        
        source = cursor.fetchone()
        
        if source:
            source_gender, source_name = source
            if source_gender == 'male':
                correct_count += 1
                print(f"  CORRECT: {bot_name} <- {source_name} ({source_gender})")
            else:
                print(f"  STILL WRONG: {bot_name} <- {source_name} ({source_gender})")
        else:
            print(f"  NO SOURCE: {bot_name}")
    
    print(f"\nFinal correct assignments: {correct_count}/{len(final_bots)}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("PRECISE MALE FIX COMPLETE!")

if __name__ == "__main__":
    precise_male_fix()
