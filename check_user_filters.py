import sqlite3

def check_user_filters():
    """Проверяем фильтры пользователя"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 547486189
    
    print("CHECKING USER FILTERS:")
    print("=" * 30)
    
    # Текущие фильтры
    cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = ?', (user_id,))
    filters = cursor.fetchone()
    
    if filters:
        gender_filter, who_pays_filter = filters
        print(f"Current filters: gender={gender_filter}, who_pays={who_pays_filter}")
    else:
        print("No filters found")
        return
    
    # Применяем фильтры как в коде
    cursor.execute('''
        SELECT user_id, name, gender, who_pays, photo_id
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = 'Kyiv'
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = 'Kyiv' AND last_rotation_date = DATE('now')))
        ORDER BY RANDOM()
        LIMIT 10
    ''', (user_id, user_id, user_id))
    
    profiles = cursor.fetchall()
    print(f"\nBase profiles: {len(profiles)}")
    
    # Применяем гендерный фильтр
    if gender_filter and gender_filter != 'all':
        profiles = [p for p in profiles if p[2] == gender_filter]
        print(f"After gender filter ({gender_filter}): {len(profiles)}")
    
    # Применяем who_pays фильтр
    if who_pays_filter and who_pays_filter != 'any':
        who_pays_mapping = {
            'i_treat': 'i_treat',
            'you_treat': 'someone_treats',
            'split': 'each_self'
        }
        db_filter_value = who_pays_mapping.get(who_pays_filter)
        if db_filter_value:
            profiles = [p for p in profiles if p[3] == db_filter_value]
            print(f"After who_pays filter ({who_pays_filter} -> {db_filter_value}): {len(profiles)}")
    
    # Показываем результат
    print(f"\nFinal profiles: {len(profiles)}")
    for i, profile in enumerate(profiles):
        user_id_bot, name, gender, who_pays, photo_id = profile
        print(f"  {i+1}. {name} ({gender}) - {who_pays}")
    
    conn.close()

if __name__ == "__main__":
    check_user_filters()
