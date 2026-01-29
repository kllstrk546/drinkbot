import sqlite3
from datetime import datetime

def simple_fix():
    """Простое исправление проблем с ботами"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 5483644714
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("SIMPLE FIX FOR KYIV BOTS:")
    print("=" * 50)
    
    # 1. Проверяем сколько ботов с фото в Киеве
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    kyiv_with_photos = cursor.fetchone()[0]
    print(f"Kyiv bots with photos: {kyiv_with_photos}")
    
    # 2. Находим ботов без фото в Киеве
    cursor.execute('''
        SELECT user_id, name, gender
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND (photo_id IS NULL OR photo_id = "")
        LIMIT 10
    ''', (city_normalized,))
    
    kyiv_bots_without_photos = cursor.fetchall()
    print(f"Kyiv bots without photos: {len(kyiv_bots_without_photos)}")
    
    # 3. Находим доступные фото из других городов
    cursor.execute('''
        SELECT photo_id
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""
        AND city_normalized != ?
        LIMIT 10
    ''', (city_normalized,))
    
    available_photos = [row[0] for row in cursor.fetchall()]
    print(f"Available photos from other cities: {len(available_photos)}")
    
    # 4. Распределяем фото
    updated_count = 0
    for i, bot in enumerate(kyiv_bots_without_photos):
        if i < len(available_photos):
            bot_id, name, gender = bot
            photo_id = available_photos[i]
            
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            updated_count += 1
            print(f"Updated {name} ({gender}) with photo")
    
    conn.commit()
    print(f"Updated {updated_count} bots with photos")
    
    # 5. Очищаем лайки и просмотры
    cursor.execute('DELETE FROM likes WHERE from_user_id = ?', (user_id,))
    cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
    conn.commit()
    
    print("Cleared user likes and views")
    
    # 6. Проверяем результат
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    found_profiles = cursor.fetchone()[0]
    print(f"Found profiles in search: {found_profiles}")
    
    # 7. Проверяем сколько ботов с фото теперь
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        AND photo_id IS NOT NULL AND photo_id != ""
    ''', (city_normalized,))
    
    final_count = cursor.fetchone()[0]
    print(f"Final Kyiv bots with photos: {final_count}")
    
    conn.close()
    
    print("FIX COMPLETE!")
    return found_profiles

if __name__ == "__main__":
    result = simple_fix()
    if result > 0:
        print("SUCCESS: Profiles found in search!")
    else:
        print("PROBLEM: Still no profiles found")
