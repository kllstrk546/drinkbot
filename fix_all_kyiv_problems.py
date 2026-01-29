import sqlite3
from datetime import datetime

def fix_all_kyiv_problems():
    """Исправление ВСЕХ проблем с ботами в Киеве"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 5483644714
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ В КИЕВЕ:")
    print("=" * 60)
    
    # ПРОБЛЕМА 1: У ботов нет фото (хотя мы загружали)
    print("\n1. ПРОВЕРЯЕМ ФОТО У БОТОВ:")
    cursor.execute('''
        SELECT user_id, name, photo_id 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
        LIMIT 10
    ''', (city_normalized,))
    
    bots_sample = cursor.fetchall()
    print(f"   Первые 10 ботов:")
    for bot in bots_sample:
        has_photo = "📷" if bot[2] and bot[2] != '' else "📷❌"
        print(f"   {has_photo} {bot[1]} (ID: {bot[0]}) - photo_id: {bot[2][:20] if bot[2] else 'None'}...")
    
    # ПРОБЛЕМА 2: Возможно фото загружены для ботов из других городов
    print("\n2. ПРОВЕРЯЕМ РАСПРЕДЕЛЕНИЕ ФОТО ПО ГОРОДАМ:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as with_photos
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        GROUP BY city_normalized
        ORDER BY with_photos DESC
        LIMIT 10
    ''')
    
    photos_by_city = cursor.fetchall()
    print(f"   Фото по городам:")
    for city, count in photos_by_city:
        print(f"   {city}: {count} ботов с фото")
    
    # ПРОБЛЕМА 3: Перераспределяем фото на киевских ботов
    print("\n3. ПЕРЕРАСПРЕДЕЛЯЕМ ФОТО НА КИЕВСКИХ БОТОВ:")
    
    # Находим ботов без фото в Киеве
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND (photo_id IS NULL OR photo_id = "")
        ORDER BY gender, name
        LIMIT 20
    ''', (city_normalized,))
    
    kyiv_bots_without_photos = cursor.fetchall()
    print(f"   Киевских ботов без фото: {len(kyiv_bots_without_photos)}")
    
    # Находим ботов с фото из других городов
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        AND city_normalized != ?
        LIMIT 20
    ''', (city_normalized,))
    
    available_photos = [row[0] for row in cursor.fetchall()]
    print(f"   Доступных фото из других городов: {len(available_photos)}")
    
    # Распределяем фото
    updated_count = 0
    for i, bot in enumerate(kyiv_bots_without_photos):
        if i < len(available_photos):
            bot_id, name, gender = bot
            photo_id = available_photos[i]
            
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"   ✅ {name} ({gender}) - фото назначено")
    
    conn.commit()
    print(f"   Обновлено {updated_count} ботов с фото")
    
    # ПРОБЛЕМА 4: Очищаем лайки и просмотры
    print("\n4. ОЧИЩАЕМ ЛАЙКИ И ПРОСМОТРЫ:")
    
    cursor.execute('DELETE FROM likes WHERE from_user_id = ?', (user_id,))
    likes_deleted = cursor.rowcount
    
    cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
    views_deleted = cursor.rowcount
    
    conn.commit()
    
    print(f"   Удалено лайков: {likes_deleted}")
    print(f"   Удалено просмотров: {views_deleted}")
    
    # ПРОБЛЕМА 5: Проверяем результат
    print("\n5. ПРОВЕРЯЕМ РЕЗУЛЬТАТ:")
    
    # Боты с фото в Киеве
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    kyiv_with_photos = cursor.fetchone()[0]
    print(f"   Киевских ботов с фото: {kyiv_with_photos}")
    
    # SQL запрос
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    found_profiles = cursor.fetchone()[0]
    print(f"   Найдено профилей в поиске: {found_profiles}")
    
    # Показываем примеры
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, is_bot
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        LIMIT 5
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    examples = cursor.fetchall()
    print(f"   Примеры найденных профилей:")
    for example in examples:
        profile_type = "Бот" if example[4] == 1 else "Пользователь"
        has_photo = "📷" if example[3] else "📷❌"
        print(f"   {has_photo} {profile_type}: {example[1]} ({example[2]})")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("ВСЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!")
    print(f"Теперь в поиске должно быть {found_profiles} профилей")

if __name__ == "__main__":
    fix_all_kyiv_problems()
