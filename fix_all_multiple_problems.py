import sqlite3
from datetime import datetime

def fix_all_multiple_problems():
    """Исправление ВСЕХ найденных проблем"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("FIXING ALL MULTIPLE PROBLEMS:")
    print("=" * 60)
    
    # ПРОБЛЕМА 1: Загружаем больше фото для киевских ботов
    print("\n1. ADDING MORE PHOTOS TO KYIV BOTS:")
    
    # Находим ботов без фото в Киеве
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND (photo_id IS NULL OR photo_id = "")
        ORDER BY gender, name
    ''', (city_normalized,))
    
    kyiv_bots_without_photos = cursor.fetchall()
    print(f"Kyiv bots without photos: {len(kyiv_bots_without_photos)}")
    
    # Находим доступные фото из других городов
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        AND city_normalized != ?
        LIMIT 30
    ''', (city_normalized,))
    
    available_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available photos from other cities: {len(available_photos)}")
    
    # Распределяем фото
    updated_count = 0
    for i, bot in enumerate(kyiv_bots_without_photos):
        if i < len(available_photos):
            bot_id, name, gender = bot
            photo_id = available_photos[i]
            
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"  Updated {name} ({gender}) with photo")
    
    conn.commit()
    print(f"Updated {updated_count} bots with photos")
    
    # ПРОБЛЕМА 2: Исправляем who_pays для женских ботов
    print("\n2. FIXING WHO_PAYS FOR FEMALE BOTS:")
    
    cursor.execute('''
        SELECT user_id, name, who_pays
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'female'
        ORDER BY name
    ''', (city_normalized,))
    
    female_bots = cursor.fetchall()
    print(f"Female bots in Kyiv: {len(female_bots)}")
    
    # Проверяем who_pays распределение
    who_pays_counts = {}
    for bot in female_bots:
        who_pays = bot[2]
        who_pays_counts[who_pays] = who_pays_counts.get(who_pays, 0) + 1
    
    print("Current who_pays distribution for female bots:")
    for wp, count in who_pays_counts.items():
        print(f"  {wp}: {count}")
    
    # Добавляем 'each_self' для ботов без правильного who_pays
    updated_who_pays = 0
    for bot in female_bots:
        bot_id, name, who_pays = bot
        if who_pays not in ['each_self', 'i_treat', 'someone_treats']:
            cursor.execute('UPDATE profiles SET who_pays = ? WHERE user_id = ?', ('each_self', bot_id))
            updated_who_pays += 1
            print(f"  Fixed who_pays for {name}")
    
    conn.commit()
    print(f"Fixed who_pays for {updated_who_pays} female bots")
    
    # ПРОБЛЕМА 3: Очищаем просмотры для обоих пользователей
    print("\n3. CLEARING VIEWS FOR BOTH USERS:")
    
    users = [547486189, 5483644714]
    
    for user_id in users:
        cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
        views_deleted = cursor.rowcount
        print(f"  User {user_id}: deleted {views_deleted} views")
    
    conn.commit()
    
    # ПРОБЛЕМА 4: Проверяем фильтры пользователей
    print("\n4. CHECKING USER FILTERS:")
    
    for user_id in users:
        cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
        user_filters = cursor.fetchone()
        
        if user_filters:
            gender_filter, who_pays_filter = user_filters
            print(f"  User {user_id}: gender={gender_filter}, who_pays={who_pays_filter}")
        else:
            print(f"  User {user_id}: no filters found")
    
    # ПРОБЛЕМА 5: Тестируем результат для обоих пользователей
    print("\n5. TESTING RESULTS FOR BOTH USERS:")
    
    for user_id in users:
        print(f"\n  USER {user_id}:")
        
        # SQL запрос
        cursor.execute('''
            SELECT COUNT(*) FROM profiles 
            WHERE user_id != ? 
            AND city_normalized = ?
            AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
            AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
            AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        ''', (user_id, city_normalized, user_id, user_id, city_normalized))
        
        sql_count = cursor.fetchone()[0]
        print(f"    SQL query finds: {sql_count} profiles")
        
        # Ручная фильтрация
        cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
        user_filters = cursor.fetchone()
        
        if user_filters:
            gender_filter, who_pays_filter = user_filters
            
            cursor.execute('''
                SELECT * FROM profiles 
                WHERE user_id != ? 
                AND city_normalized = ?
                AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
                AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
                AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
            ''', (user_id, city_normalized, user_id, user_id, city_normalized))
            
            results = cursor.fetchall()
            
            # Применяем фильтры
            filtered_count = 0
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
                
                filtered_count += 1
            
            print(f"    After manual filtering: {filtered_count} profiles")
    
    # ПРОБЛЕМА 6: Финальная статистика
    print("\n6. FINAL STATISTICS:")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    final_photo_count = cursor.fetchone()[0]
    print(f"  Final Kyiv bots with photos: {final_photo_count}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND gender = 'female' AND who_pays = 'each_self'
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    ideal_female_bots = cursor.fetchone()[0]
    print(f"  Ideal female bots (photo + each_self): {ideal_female_bots}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("ALL PROBLEMS FIXED!")
    print("Both users should now see more profiles with photos!")

if __name__ == "__main__":
    fix_all_multiple_problems()
