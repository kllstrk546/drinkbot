import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

user_id = 5483644714
city_normalized = 'Kyiv'

# Точный запрос из get_profiles_for_swiping_by_city_exact
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
    LIMIT ?
'''

params = (user_id, city_normalized, user_id, user_id, city_normalized, 10)

print(f'Query: {query}')
print(f'Params: {params}')

cursor.execute(query, params)
results = cursor.fetchall()

print(f'\nFound {len(results)} profiles:')

for i, result in enumerate(results):
    print(f'  Profile {i+1}:')
    print(f'    ID: {result[1]}')  # user_id
    print(f'    Name: {result[2]}')  # name
    print(f'    Gender: {result[16]}')  # gender
    print(f'    City: {result[4]}')  # city
    print(f'    City Normalized: {result[6]}')  # city_normalized
    print(f'    Is Bot: {result[19]}')  # is_bot
    print(f'    Who Pays: {result[9]}')  # who_pays
    print(f'    Last Rotation: {result[21]}')  # last_rotation_date
    print()

# Теперь проверим каждого условия отдельно для нашего бота
bot_id = -9999999
cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (bot_id,))
bot = cursor.fetchone()

if bot:
    print(f'=== CHECKING BOT CONDITIONS STEP BY STEP ===')
    
    # Условие 1: user_id != ?
    cond1 = bot[1] != user_id
    print(f'1. user_id != {user_id}: {cond1}')
    
    # Условие 2: city_normalized = ?
    cond2 = bot[6] == city_normalized
    print(f'2. city_normalized == {city_normalized}: {cond2}')
    
    # Условие 3: NOT IN likes
    cursor.execute('SELECT COUNT(*) FROM likes WHERE from_user_id = ? AND to_user_id = ?', (user_id, bot_id))
    likes_count = cursor.fetchone()[0]
    cond3 = likes_count == 0
    print(f'3. NOT IN likes: {cond3} (likes count: {likes_count})')
    
    # Условие 4: NOT IN profile_views
    cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND profile_id = ? AND view_date = DATE("now")', (user_id, bot_id))
    views_count = cursor.fetchone()[0]
    cond4 = views_count == 0
    print(f'4. NOT IN profile_views: {cond4} (views count: {views_count})')
    
    # Условие 5: (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
    cond5 = (bot[19] == 0) or (bot[6] == city_normalized and bot[21] == '2026-01-29')
    print(f'5. Bot condition: {cond5} (is_bot={bot[19]}, city_normalized={bot[6]}, last_rotation_date={bot[21]})')
    
    all_conditions = cond1 and cond2 and cond3 and cond4 and cond5
    print(f'\nALL CONDITIONS: {all_conditions}')

conn.close()
