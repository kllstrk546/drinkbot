import sqlite3
from datetime import datetime

def fix_all_problems():
    """Исправление всех найденных проблем"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    city_normalized = 'Kyiv'
    user_id = 5483644714
    
    print("ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ:")
    print("=" * 50)
    
    # ПРОБЛЕМА 1: У ботов нет даты ротации
    print("\n1. Устанавливаем дату ротации для всех ботов...")
    cursor.execute('UPDATE profiles SET last_rotation_date = ? WHERE is_bot = 1', (today,))
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?', (today,))
    updated_count = cursor.fetchone()[0]
    print(f"   Обновлено ботов с датой ротации: {updated_count}")
    
    # ПРОБЛЕМА 2: Очищаем просмотры пользователя
    print("\n2. Очищаем просмотры пользователя...")
    cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ?', (user_id,))
    views_count = cursor.fetchone()[0]
    print(f"   Осталось просмотров: {views_count}")
    
    # ПРОБЛЕМА 3: Проверяем результат
    print("\n3. Проверяем результат поиска...")
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    found_count = cursor.fetchone()[0]
    print(f"   Найдено профилей после исправлений: {found_count}")
    
    # ПРОБЛЕМА 4: Проверяем ботов в Киеве
    print("\n4. Проверяем ботов в Киеве...")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?', (city_normalized, today))
    kyiv_bots = cursor.fetchone()[0]
    print(f"   Активных ботов в Киеве: {kyiv_bots}")
    
    # ПРОБЛЕМА 5: Показываем примеры найденных профилей
    print("\n5. Примеры найденных профилей:")
    cursor.execute('''
        SELECT user_id, name, age, gender, is_bot 
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        LIMIT 5
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    profiles = cursor.fetchall()
    for i, profile in enumerate(profiles):
        profile_type = "Бот" if profile[4] == 1 else "Пользователь"
        print(f"   {i+1}. {profile_type}: ID={profile[0]}, {profile[1]}, {profile[2]}, {profile[3]}")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("ВСЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!")
    print(f"Теперь должно найтись {found_count} профилей")

if __name__ == "__main__":
    fix_all_problems()
