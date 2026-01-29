import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим viewed profiles для user_id = 547486189
cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = 547486189 AND view_date = DATE("now")')
viewed_count = cursor.fetchone()[0]
print(f'User 547486189 viewed profiles today: {viewed_count}')

# Очистим viewed profiles для этого пользователя
cursor.execute('DELETE FROM profile_views WHERE user_id = 547486189')
conn.commit()
print('Cleared viewed profiles for user 547486189')

# Проверим есть ли лайки от этого пользователя
cursor.execute('SELECT COUNT(*) FROM likes WHERE from_user_id = 547486189')
likes_count = cursor.fetchone()[0]
print(f'User 547486189 likes: {likes_count}')

# Теперь проверим прямой запрос с фильтрами пользователя
print('\nTesting direct query with user filters:')

# Получим фильтры пользователя
cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = 547486189')
filters = cursor.fetchone()

if filters:
    gender_filter = filters[0] or 'all'
    who_pays_filter = filters[1] or 'any'
    print(f'User filters: gender={gender_filter}, who_pays={who_pays_filter}')
    
    # Выполним точный запрос как в функции
    who_pays_mapping = {
        'i_treat': 'i_treat',
        'you_treat': 'someone_treats',
        'split': 'each_self',
        'any': None
    }
    
    conditions = ["p.user_id != ?", "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)"]
    params = [547486189, 547486189]
    
    conditions.append("p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))")
    params.append(547486189)
    
    # Городской фильтр
    all_cities = ['Kyiv', 'Kharkiv', 'Odesa', 'Lviv', 'Dnipro']
    city_placeholders = ','.join(['?' for _ in all_cities])
    conditions.append(f"p.city_normalized IN ({city_placeholders})")
    params.extend(all_cities)
    
    # Условие для ботов
    conditions.append("(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))")
    params.append('Kyiv')
    
    # Гендерный фильтр
    if gender_filter and gender_filter != 'all':
        conditions.append("p.gender = ?")
        params.append(gender_filter)
    
    # Фильтр who_pays
    if who_pays_filter and who_pays_filter != 'any':
        mapped_value = who_pays_mapping.get(who_pays_filter)
        if mapped_value:
            conditions.append("p.who_pays = ?")
            params.append(mapped_value)
    
    query = f'''
        SELECT p.* FROM profiles p
        WHERE {' AND '.join(conditions)}
        ORDER BY RANDOM()
        LIMIT 10
    '''
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    print(f'Query found {len(results)} profiles')
    
    for i, result in enumerate(results[:3]):
        print(f'  Profile {i+1}: ID={result[0]}, Name={result[3]}, Gender={result[5]}, City={result[6]}, IsBot={result[13]}, WhoPays={result[11]}')

conn.close()
