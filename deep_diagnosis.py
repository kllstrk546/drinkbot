import sqlite3
from datetime import datetime

def deep_diagnosis():
    """Глубокая диагностика ВСЕХ проблем"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    # Проверяем ОБАИХ пользователей
    users = [547486189, 5483644714]
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("DEEP DIAGNOSIS - ALL PROBLEMS:")
    print("=" * 60)
    
    for user_id in users:
        print(f"\n=== USER {user_id} ===")
        
        # 1. Проверяем лайки и просмотры
        cursor.execute('SELECT COUNT(*) FROM likes WHERE from_user_id = ?', (user_id,))
        likes_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND view_date = ?', (user_id, today))
        views_count = cursor.fetchone()[0]
        
        print(f"Likes: {likes_count}, Views today: {views_count}")
        
        # 2. Проверяем SQL запрос
        cursor.execute('''
            SELECT * FROM profiles 
            WHERE user_id != ? 
            AND city_normalized = ?
            AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
            AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
            AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
            ORDER BY RANDOM()
            LIMIT 10
        ''', (user_id, city_normalized, user_id, user_id, city_normalized))
        
        results = cursor.fetchall()
        print(f"SQL query finds: {len(results)} profiles")
        
        # 3. Анализируем каждый найденный профиль
        print("Found profiles:")
        for i, result in enumerate(results):
            profile_id = result[1]
            name = result[2]
            is_bot = result[19]
            photo_id = result[8]
            
            profile_type = "BOT" if is_bot == 1 else "USER"
            has_photo = "YES" if photo_id else "NO"
            
            print(f"  {i+1}. {profile_type}: {name} (ID: {profile_id}) - Photo: {has_photo}")
            
            if photo_id:
                print(f"      Photo ID: {photo_id[:30]}...")
        
        # 4. Проверяем ручную фильтрацию
        print("Manual filtering check:")
        
        # Получаем фильтры пользователя
        cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
        user_filters = cursor.fetchone()
        
        if user_filters:
            gender_filter, who_pays_filter = user_filters
            print(f"User filters: gender={gender_filter}, who_pays={who_pays_filter}")
            
            # Применяем фильтры
            filtered_results = []
            for result in results:
                profile_gender = result[16]
                profile_who_pays = result[9]
                
                # Gender filter
                if gender_filter and gender_filter != 'all':
                    if profile_gender != gender_filter:
                        continue
                
                # Who pays filter
                if who_pays_filter and who_pays_filter != 'any':
                    who_pays_mapping = {
                        'i_treat': 'i_treat',
                        'you_treat': 'someone_treats',
                        'split': 'each_self'
                    }
                    db_filter_value = who_pays_mapping.get(who_pays_filter)
                    if db_filter_value and profile_who_pays != db_filter_value:
                        continue
                
                filtered_results.append(result)
            
            print(f"After manual filtering: {len(filtered_results)} profiles")
        else:
            print("No user filters found")
    
    # 5. Проверяем ВСЕХ ботов в Киеве
    print(f"\n=== ALL KYIV BOTS ===")
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
    ''', (city_normalized,))
    
    all_bots = cursor.fetchall()
    print(f"Total bots in Kyiv: {len(all_bots)}")
    
    male_bots = [b for b in all_bots if b[2] == 'male']
    female_bots = [b for b in all_bots if b[2] == 'female']
    
    print(f"Male bots: {len(male_bots)}")
    print(f"Female bots: {len(female_bots)}")
    
    # 6. Проверяем ботов с фото
    bots_with_photos = [b for b in all_bots if b[3] and b[3] != '']
    print(f"Bots with photos: {len(bots_with_photos)}")
    
    # 7. Проверяем активных ботов
    active_bots = [b for b in all_bots if b[4] == today]
    print(f"Active bots today: {len(active_bots)}")
    
    # 8. Идеальные кандидаты (активные + фото)
    ideal_bots = [b for b in active_bots if b[3] and b[3] != '']
    print(f"Ideal bots (active + photo): {len(ideal_bots)}")
    
    # 9. Показываем примеры идеальных ботов
    print("Ideal bot examples:")
    for i, bot in enumerate(ideal_bots[:5]):
        print(f"  {i+1}. {bot[1]} ({bot[2]}) - Photo: {bot[3][:30] if bot[3] else 'None'}...")
    
    # 10. Проверяем распределение фото по городам
    print(f"\n=== PHOTO DISTRIBUTION ===")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as with_photos
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        GROUP BY city_normalized
        ORDER BY with_photos DESC
        LIMIT 10
    ''')
    
    photo_distribution = cursor.fetchall()
    for city, count in photo_distribution:
        print(f"  {city}: {count} bots with photos")
    
    conn.close()

if __name__ == "__main__":
    deep_diagnosis()
