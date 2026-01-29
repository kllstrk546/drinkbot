import sqlite3
from datetime import datetime

def debug_kyiv_single_profile():
    """Диагностика почему только один профиль в Киеве"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 547486189
    city_normalized = 'Kyiv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("DEBUG: ПОЧЕМУ ТОЛЬКО ОДИН ПРОФИЛЬ В КИЕВЕ")
    print("=" * 60)
    
    # 1. Проверяем фильтры пользователя
    print("\n1. ФИЛЬТРЫ ПОЛЬЗОВАТЕЛЯ:")
    cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
    user_filters = cursor.fetchone()
    
    if user_filters:
        gender_filter, who_pays_filter = user_filters
        print(f"   User {user_id}: gender={gender_filter}, who_pays={who_pays_filter}")
    else:
        print(f"   User {user_id}: ФИЛЬТРЫ НЕ НАЙДЕНЫ")
        return
    
    # 2. Все боты в Киеве
    print("\n2. ВСЕ БОТЫ В КИЕВЕ:")
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date, who_pays
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ?
        ORDER BY gender, name
    ''', (city_normalized,))
    
    all_bots = cursor.fetchall()
    print(f"   Всего ботов в Киеве: {len(all_bots)}")
    
    male_bots = [b for b in all_bots if b[2] == 'male']
    female_bots = [b for b in all_bots if b[2] == 'female']
    
    print(f"   Мужских ботов: {len(male_bots)}")
    print(f"   Женских ботов: {len(female_bots)}")
    
    # 3. Активные боты сегодня
    print("\n3. АКТИВНЫЕ БОТЫ СЕГОДНЯ:")
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date, who_pays
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
        ORDER BY gender, name
    ''', (city_normalized, today))
    
    active_bots = cursor.fetchall()
    print(f"   Активных ботов сегодня: {len(active_bots)}")
    
    active_male = [b for b in active_bots if b[2] == 'male']
    active_female = [b for b in active_bots if b[2] == 'female']
    
    print(f"   Активных мужчин: {len(active_male)}")
    print(f"   Активных женщин: {len(active_female)}")
    
    # 4. Исключенные по лайкам
    print("\n4. ИСКЛЮЧЕННЫЕ ПО ЛАЙКАМ:")
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 
        AND p.city_normalized = ?
        AND p.user_id IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
    ''', (city_normalized, user_id))
    
    liked_count = cursor.fetchone()[0]
    print(f"   Исключено по лайкам: {liked_count}")
    
    # 5. Исключенные по просмотрам
    print("\n5. ИСКЛЮЧЕННЫЕ ПО ПРОСМОТРАМ СЕГОДНЯ:")
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 
        AND p.city_normalized = ?
        AND p.user_id IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (city_normalized, user_id))
    
    viewed_count = cursor.fetchone()[0]
    print(f"   Исключено по просмотрам сегодня: {viewed_count}")
    
    # 6. Применяем фильтры
    print("\n6. ПРИМЕНЯЕМ ФИЛЬТРЫ:")
    
    # Начинаем с активных ботов
    available = active_bots.copy()
    print(f"   Начинаем с активных ботов: {len(available)}")
    
    # Исключаем лайкнутые
    available = [b for b in available if b[0] not in [
        row[0] for row in cursor.execute('SELECT to_user_id FROM likes WHERE from_user_id = ?', (user_id,)).fetchall()
    ]]
    print(f"   После исключения лайков: {len(available)}")
    
    # Исключенные просмотренные сегодня
    available = [b for b in available if b[0] not in [
        row[0] for row in cursor.execute('SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE("now")', (user_id,)).fetchall()
    ]]
    print(f"   После исключения просмотров: {len(available)}")
    
    # Гендерный фильтр
    if gender_filter != 'all':
        available = [b for b in available if b[2] == gender_filter]
        print(f"   После гендерного фильтра ({gender_filter}): {len(available)}")
    
    # Who pays фильтр
    if who_pays_filter != 'any':
        who_pays_mapping = {
            'i_treat': 'i_treat',
            'you_treat': 'someone_treats',
            'split': 'each_self'
        }
        db_filter_value = who_pays_mapping.get(who_pays_filter)
        if db_filter_value:
            available = [b for b in available if b[5] == db_filter_value]
            print(f"   После who_pays фильтра ({who_pays_filter} -> {db_filter_value}): {len(available)}")
    
    # 7. Показываем финальный результат
    print("\n7. ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print(f"   Доступно профилей: {len(available)}")
    
    if available:
        print("   Доступные профили:")
        for i, bot in enumerate(available):
            user_id_bot, name, gender, photo_id, rotation_date, who_pays = bot
            print(f"     {i+1}. {name} ({gender}) - {who_pays} - {photo_id[:30] if photo_id else 'NO PHOTO'}...")
    else:
        print("   НЕТ ДОСТУПНЫХ ПРОФИЛЕЙ!")
    
    # 8. Рекомендации
    print("\n8. РЕКОМЕНДАЦИИ:")
    
    if len(active_bots) < 10:
        print("   ❌ МАЛО АКТИВНЫХ БОТОВ - НУЖНА РОТАЦИЯ")
        print("   Запусти: python quick_rotation.py")
    
    if liked_count > 5:
        print("   ❌ МНОГО ЛАЙКОВ - ОЧИСТИ ИСТОРИЮ")
        print("   Запусти: python clear_user_history.py")
    
    if viewed_count > 5:
        print("   ❌ МНОГО ПРОСМОТРОВ - ПОДОЖДИ ЗАВТРА")
    
    if gender_filter != 'all':
        print(f"   ❌ СТРОГИЙ ГЕНДЕРНЫЙ ФИЛЬТР: {gender_filter}")
        print("   Попробуй: gender='all'")
    
    if who_pays_filter != 'any':
        print(f"   ❌ СТРОГИЙ WHO_PAYS ФИЛЬТР: {who_pays_filter}")
        print("   Попробуй: who_pays='any'")
    
    conn.close()

if __name__ == "__main__":
    debug_kyiv_single_profile()
