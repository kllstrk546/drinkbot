import sqlite3
from datetime import datetime

def complete_diagnosis():
    """Полная диагностика ВСЕХ проблем с ботами и поиском"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 5483644714
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("=" * 80)
    print("ПОЛНАЯ ДИАГНОСТИКА ВСЕХ ПРОБЛЕМ")
    print("=" * 80)
    
    # 1. Проверяем ВСЕХ ботов в Киеве
    print("\n1. ВСЕ БОТЫ В КИЕВЕ:")
    cursor.execute('''
        SELECT user_id, name, age, gender, photo_id, last_rotation_date
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
    ''', (city_normalized,))
    
    all_kyiv_bots = cursor.fetchall()
    print(f"   Всего ботов в Киеве: {len(all_kyiv_bots)}")
    
    male_bots = [b for b in all_kyiv_bots if b[3] == 'male']
    female_bots = [b for b in all_kyiv_bots if b[3] == 'female']
    
    print(f"   Мужских ботов: {len(male_bots)}")
    print(f"   Женских ботов: {len(female_bots)}")
    
    # 2. Проверяем активных ботов
    print("\n2. АКТИВНЫЕ БОТЫ (с датой ротации):")
    active_bots = [b for b in all_kyiv_bots if b[5] == today]
    print(f"   Активных ботов сегодня: {len(active_bots)}")
    
    # 3. Проверяем ботов с фото
    print("\n3. БОТЫ С ФОТО:")
    bots_with_photos = [b for b in all_kyiv_bots if b[4] and b[4] != '']
    print(f"   Ботов с фото: {len(bots_with_photos)}")
    
    # 4. Проверяем пересечение - активные боты с фото
    print("\n4. АКТИВНЫЕ БОТЫ С ФОТО (идеальные кандидаты):")
    active_with_photos = [b for b in active_bots if b[4] and b[4] != '']
    print(f"   Активных ботов с фото: {len(active_with_photos)}")
    
    # 5. Проверяем лайки пользователя
    print("\n5. ЛАЙКИ ПОЛЬЗОВАТЕЛЯ:")
    cursor.execute('SELECT to_user_id FROM likes WHERE from_user_id = ?', (user_id,))
    user_likes = [like[0] for like in cursor.fetchall()]
    print(f"   Всего лайков пользователя: {len(user_likes)}")
    
    # 6. Проверяем просмотры пользователя
    print("\n6. ПРОСМОТРЫ ПОЛЬЗОВАТЕЛЯ:")
    cursor.execute('SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = ?', (user_id, today))
    user_views = [view[0] for view in cursor.fetchall()]
    print(f"   Просмотров сегодня: {len(user_views)}")
    
    # 7. Тестируем полный SQL запрос из get_profiles_for_swiping_by_city_exact
    print("\n7. ПОЛНЫЙ SQL ЗАПРОС (get_profiles_for_swiping_by_city_exact):")
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
    
    # 8. Анализируем почему каждый бот исключается
    print("\n8. АНАЛИЗ ИСКЛЮЧЕНИЯ БОТОВ:")
    for bot in all_kyiv_bots[:10]:  # Анализируем первые 10
        bot_id, name, age, gender, photo_id, rotation_date = bot
        reasons = []
        
        if bot_id == user_id:
            reasons.append("user_id == bot_id")
        
        if rotation_date != today:
            reasons.append(f"rotation_date != today ({rotation_date})")
        
        if bot_id in user_likes:
            reasons.append("bot in user_likes")
        
        if bot_id in user_views:
            reasons.append("bot in user_views")
        
        status = "✅ ПОДХОДИТ" if not reasons else f"❌ {', '.join(reasons)}"
        photo_status = "📷" if photo_id else "📷❌"
        
        print(f"   {photo_status} {name} ({gender}, {age}) - {status}")
    
    # 9. Проверяем реальные профили
    print("\n9. РЕАЛЬНЫЕ ПРОФИЛИ В КИЕВЕ:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 0 AND city_normalized = ?', (city_normalized,))
    real_users = cursor.fetchone()[0]
    print(f"   Реальных пользователей: {real_users}")
    
    # 10. Проверяем общую статистику
    print("\n10. ОБЩАЯ СТАТИСТИКА:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1')
    total_bots = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""')
    total_with_photos = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?', (today,))
    total_active = cursor.fetchone()[0]
    
    print(f"   Всего ботов в системе: {total_bots}")
    print(f"   Всего ботов с фото: {total_with_photos}")
    print(f"   Всего активных ботов: {total_active}")
    
    # 11. Ищем конкретные проблемы
    print("\n11. КОНКРЕТНЫЕ ПРОБЛЕМЫ:")
    problems = []
    
    if len(active_bots) < len(all_kyiv_bots):
        problems.append(f"❌ {len(all_kyiv_bots) - len(active_bots)} ботов неактивны (нет даты ротации)")
    
    if len(bots_with_photos) < len(all_kyiv_bots):
        problems.append(f"❌ {len(all_kyiv_bots) - len(bots_with_photos)} ботов без фото")
    
    if len(active_with_photos) < len(active_bots):
        problems.append(f"❌ {len(active_bots) - len(active_with_photos)} активных ботов без фото")
    
    if len(results) == 0:
        problems.append("❌ SQL запрос находит 0 профилей")
    elif len(results) < 5:
        problems.append(f"⚠️  SQL запрос находит мало профилей: {len(results)}")
    
    if user_likes:
        problems.append(f"⚠️  Пользователь лайкал {len(user_likes)} профилей")
    
    if user_views:
        problems.append(f"⚠️  Пользователь просматривал {len(user_views)} профилей")
    
    if problems:
        for problem in problems:
            print(f"   {problem}")
    else:
        print("   ✅ Явных проблем не найдено")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("РЕКОМЕНДАЦИИ:")
    
    if len(active_bots) < len(all_kyiv_bots):
        print("1. ОБНОВИТЬ ДАТУ РОТАЦИИ для всех ботов в Киеве")
    
    if len(bots_with_photos) < len(all_kyiv_bots):
        print("2. ЗАГРУЗИТЬ ФОТО для ботов без фото")
    
    if len(results) == 0:
        print("3. ПРОВЕРИТЬ SQL запрос и фильтры")
    
    if user_likes or user_views:
        print("4. ОЧИСТИТЬ лайки и просмотры пользователя")

if __name__ == "__main__":
    complete_diagnosis()
