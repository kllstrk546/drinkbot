import sqlite3
from datetime import datetime

def full_diagnosis():
    """Полная диагностика всех проблем с поиском"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 5483644714
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 60)
    print("ПОЛНАЯ ДИАГНОСТИКА ПРОБЛЕМ С ПОИСКОМ")
    print("=" * 60)
    
    # 1. Проверяем ботов в Киеве
    print("\n1. БОТЫ В КИЕВЕ:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = ?', (city_normalized,))
    total_bots = cursor.fetchone()[0]
    print(f"   Всего ботов в Киеве: {total_bots}")
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?', (city_normalized, today))
    active_bots = cursor.fetchone()[0]
    print(f"   Активных ботов сегодня: {active_bots}")
    
    # 2. Проверяем реальные профили в Киеве
    print("\n2. РЕАЛЬНЫЕ ПРОФИЛИ В КИЕВЕ:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 0 AND city_normalized = ?', (city_normalized,))
    real_users = cursor.fetchone()[0]
    print(f"   Реальных пользователей в Киеве: {real_users}")
    
    # 3. Проверяем лайки пользователя
    print("\n3. ЛАЙКИ ПОЛЬЗОВАТЕЛЯ:")
    cursor.execute('SELECT COUNT(*) FROM likes WHERE from_user_id = ?', (user_id,))
    user_likes = cursor.fetchone()[0]
    print(f"   Лайков пользователя: {user_likes}")
    
    # 4. Проверяем просмотры пользователя
    print("\n4. ПРОСМОТРЫ ПОЛЬЗОВАТЕЛЯ:")
    cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND view_date = ?', (user_id, today))
    user_views = cursor.fetchone()[0]
    print(f"   Просмотров сегодня: {user_views}")
    
    # 5. Тестируем get_profiles_for_swiping_by_city_exact (функция из "🌍 В других городах")
    print("\n5. ТЕСТ get_profiles_for_swiping_by_city_exact:")
    query = '''
        SELECT * FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        AND user_id NOT IN (
            SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
        )
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        ORDER BY RANDOM()
        LIMIT 10
    '''
    params = (user_id, city_normalized, user_id, user_id, city_normalized)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    print(f"   Найдено профилей: {len(results)}")
    
    for i, result in enumerate(results[:3]):  # Показываем первые 3
        print(f"   Профиль {i+1}: ID={result[1]}, Name={result[2]}, IsBot={result[19]}")
    
    # 6. Проверяем каждый фильтр отдельно
    print("\n6. ПОШАГОВАЯ ПРОВЕРКА ФИЛЬТРОВ:")
    
    # Фильтр 1: user_id != ?
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE user_id != ?', (user_id,))
    step1 = cursor.fetchone()[0]
    print(f"   После user_id != {user_id}: {step1}")
    
    # Фильтр 2: city_normalized = ?
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE user_id != ? AND city_normalized = ?', (user_id, city_normalized))
    step2 = cursor.fetchone()[0]
    print(f"   После city_normalized = {city_normalized}: {step2}")
    
    # Фильтр 3: NOT IN likes
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
    ''', (user_id, city_normalized, user_id))
    step3 = cursor.fetchone()[0]
    print(f"   После NOT IN likes: {step3}")
    
    # Фильтр 4: NOT IN profile_views
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (user_id, city_normalized, user_id, user_id))
    step4 = cursor.fetchone()[0]
    print(f"   После NOT IN profile_views: {step4}")
    
    # Фильтр 5: bot condition
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE user_id != ? AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    step5 = cursor.fetchone()[0]
    print(f"   После bot condition: {step5}")
    
    # 7. Проверяем конкретных ботов
    print("\n7. КОНКРЕТНЫЕ БОТЫ В КИЕВЕ:")
    cursor.execute('''
        SELECT user_id, name, age, gender, last_rotation_date 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? 
        LIMIT 5
    ''', (city_normalized,))
    
    bots = cursor.fetchall()
    for bot in bots:
        print(f"   Бот ID={bot[0]}: {bot[1]}, {bot[2]}, {bot[3]}, rotation={bot[4]}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("АНАЛИЗ ПРОБЛЕМ:")
    if step2 == 0:
        print("❌ ПРОБЛЕМА: Нет профилей в Киеве с city_normalized = 'Kyiv'")
    elif step3 == 0:
        print("❌ ПРОБЛЕМА: Все профили залайканы пользователем")
    elif step4 == 0:
        print("❌ ПРОБЛЕМА: Все профили просмотрены пользователем")
    elif step5 == 0:
        print("❌ ПРОБЛЕМА: Нет активных ботов с правильной датой ротации")
    else:
        print("✅ Все фильтры проходят, проблема в другом месте")

if __name__ == "__main__":
    full_diagnosis()
