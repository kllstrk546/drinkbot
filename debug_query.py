import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Точный запрос как в функции get_profiles_for_swiping_with_filters
user_id = 547486189
city_normalized = 'Kyiv'
gender_filter = 'female'
who_pays_filter = 'split'

conditions = ["p.user_id != ?", "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)"]
params = [user_id, user_id]

conditions.append("p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))")
params.append(user_id)

# Городской фильтр
all_cities = ['Kyiv', 'Kharkiv', 'Odesa', 'Lviv', 'Dnipro']
city_placeholders = ','.join(['?' for _ in all_cities])
conditions.append(f"p.city_normalized IN ({city_placeholders})")
params.extend(all_cities)

# Условие для ботов
conditions.append("(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))")
params.append(city_normalized)

# Гендерный фильтр
if gender_filter and gender_filter != 'all':
    conditions.append("p.gender = ?")
    params.append(gender_filter)

# Фильтр who_pays
who_pays_mapping = {
    'i_treat': 'i_treat',
    'you_treat': 'someone_treats',
    'split': 'each_self',
    'any': None
}

if who_pays_filter and who_pays_filter != 'any':
    mapped_value = who_pays_mapping.get(who_pays_filter)
    if mapped_value:
        conditions.append("p.who_pays = ?")
        params.append(mapped_value)

print(f'Conditions: {conditions}')
print(f'Params: {params}')

query = f'''
    SELECT p.* FROM profiles p
    WHERE {' AND '.join(conditions)}
    ORDER BY RANDOM()
    LIMIT 10
'''

print(f'\nQuery: {query}')

cursor.execute(query, params)
results = cursor.fetchall()

print(f'\nFound {len(results)} profiles')

for i, result in enumerate(results):
    print(f'  Profile {i+1}:')
    print(f'    ID: {result[0]}')
    print(f'    Name: {result[3]}')
    print(f'    Age: {result[4]}')
    print(f'    Gender: {result[5]}')
    print(f'    City: {result[6]}')
    print(f'    City Normalized: {result[8]}')
    print(f'    Who Pays: {result[11]}')
    print(f'    Is Bot: {result[13]}')
    print(f'    Last Rotation: {result[16]}')
    print()

# Теперь проверим конкретного бота
bot_id = -2950106
cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (bot_id,))
bot_profile = cursor.fetchone()

if bot_profile:
    print(f'Bot {bot_id} details:')
    print(f'  Name: {bot_profile[3]}')
    print(f'  Gender: {bot_profile[5]}')
    print(f'  City: {bot_profile[6]}')
    print(f'  City Normalized: {bot_profile[8]}')
    print(f'  Who Pays: {bot_profile[11]}')
    print(f'  Is Bot: {bot_profile[13]}')
    print(f'  Last Rotation: {bot_profile[16]}')
    
    # Проверим проходит ли бот все условия
    print(f'\nBot condition checks:')
    print(f'  user_id != {user_id}: {bot_profile[0] != user_id}')
    print(f'  not in likes: {bot_profile[0] not in [1249551181, 5483644714, 5751546628, 5933537042]}')
    print(f'  city_normalized == Kyiv: {bot_profile[8] == "Kyiv"}')
    print(f'  gender == female: {bot_profile[5] == "female"}')
    print(f'  who_pays == each_self: {bot_profile[11] == "each_self"}')
    print(f'  last_rotation_date == today: {bot_profile[16] == "2026-01-29"}')

conn.close()
