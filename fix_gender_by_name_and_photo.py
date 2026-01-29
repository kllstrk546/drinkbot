import sqlite3

def fix_gender_by_name_and_photo():
    """Исправляем gender по имени и photo_id"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("FIXING GENDER BY NAME AND PHOTO:")
    print("=" * 50)
    
    # 1. Находим всех ботов с неправильным gender
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, p.photo_id, p.bot_photo_path
        FROM profiles p
        WHERE p.is_bot = 1 
        AND p.photo_id IS NOT NULL AND p.photo_id != ''
        ORDER BY p.user_id
    ''')
    
    all_bots = cursor.fetchall()
    print(f"Total bots with photos: {len(all_bots)}")
    
    # 2. Группируем по photo_id чтобы определить правильный gender
    photo_gender_map = {}
    
    for bot in all_bots:
        user_id, name, gender, photo_id, bot_photo_path = bot
        
        # Определяем gender по имени
        name_lower = name.lower()
        name_gender = None
        
        # Женские имена (простые проверки)
        female_names = ['анна', 'мария', 'елена', 'ольга', 'наталья', 'екатерина', 'светлана', 'ирина', 'татьяна', 'юлия',
                       'александра', 'ксения', 'дарья', 'вероника', 'виктория', 'полина', 'анастасия', 'маргарита', 'евгения',
                       'анастасия', 'валентина', 'зоя', 'лидия', 'лариса', 'инна', 'оксана', 'юлия', 'алена', 'алла']
        
        male_names = ['александр', 'дмитрий', 'максим', 'иван', 'артем', 'никита', 'михаил', 'даниил', 'егор', 'андрей',
                     'алексей', 'кирилл', 'матвей', 'илья', 'тимофей', 'роман', 'павел', 'евгений', 'сергей', 'владимир',
                     'владислав', 'ян', 'григорий', 'валентин', 'виктор', 'юрий', 'федор', 'константин', 'станислав', 'олег']
        
        if any(female_name in name_lower for female_name in female_names):
            name_gender = 'female'
        elif any(male_name in name_lower for male_name in male_names):
            name_gender = 'male'
        else:
            # Если имя не определилось, используем bot_photo_path
            if bot_photo_path:
                if 'female' in bot_photo_path.lower():
                    name_gender = 'female'
                elif 'male' in bot_photo_path.lower():
                    name_gender = 'male'
        
        # Определяем gender по photo_id (ищем другие боты с таким же photo_id)
        if photo_id not in photo_gender_map:
            cursor.execute('''
                SELECT COUNT(*) as male_count, COUNT(*) as female_count
                FROM profiles 
                WHERE photo_id = ? AND is_bot = 1
            ''', (photo_id,))
            
            # Просто считаем сколько ботов с этим photo_id
            cursor.execute('''
                SELECT gender, COUNT(*) 
                FROM profiles 
                WHERE photo_id = ? AND is_bot = 1
                GROUP BY gender
            ''', (photo_id,))
            
            photo_genders = cursor.fetchall()
            male_count = sum(cnt for gender, cnt in photo_genders if gender == 'male')
            female_count = sum(cnt for gender, cnt in photo_genders if gender == 'female')
            
            if female_count > male_count:
                photo_gender_map[photo_id] = 'female'
            elif male_count > female_count:
                photo_gender_map[photo_id] = 'male'
            else:
                photo_gender_map[photo_id] = name_gender  # Если поровну, используем gender по имени
        
        # 3. Проверяем нужно ли исправлять
        current_gender = gender
        correct_gender = name_gender or photo_gender_map.get(photo_id, current_gender)
        
        if current_gender != correct_gender:
            print(f"FIXING: {name} ({current_gender}) -> {correct_gender}")
            print(f"  Photo: {photo_id[:30] if photo_id else 'NO PHOTO'}...")
            print(f"  Path: {bot_photo_path}")
            
            # Исправляем gender
            cursor.execute('UPDATE profiles SET gender = ? WHERE user_id = ?', (correct_gender, user_id))
    
    conn.commit()
    
    # 4. Проверяем результат
    print("\nAFTER FIXING:")
    cursor.execute('''
        SELECT gender, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY gender
        ORDER BY gender
    ''')
    
    gender_dist = cursor.fetchall()
    print("Gender distribution:")
    for gender, count in gender_dist:
        print(f"  {gender}: {count}")
    
    # 5. Проверяем киевских ботов
    cursor.execute('''
        SELECT gender, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY gender
        ORDER BY gender
    ''')
    
    kyiv_gender_dist = cursor.fetchall()
    print("\nKyiv gender distribution:")
    for gender, count in kyiv_gender_dist:
        print(f"  {gender}: {count}")
    
    # 6. Показываем примеры
    print("\nSample female bots:")
    cursor.execute('''
        SELECT name, gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND gender = 'female' AND photo_id IS NOT NULL AND photo_id != ''
        LIMIT 5
    ''')
    
    female_samples = cursor.fetchall()
    for name, gender, photo_id in female_samples:
        print(f"  {name} ({gender}) - {photo_id[:30] if photo_id else 'NO PHOTO'}...")
    
    conn.close()
    print("\nGENDER FIXING COMPLETE!")

if __name__ == "__main__":
    fix_gender_by_name_and_photo()
