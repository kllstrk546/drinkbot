import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

user_id = 5483644714
city_normalized = 'Kyiv'

print(f'=== DEBUGGING SQL QUERY FOR BOTS ===')

# Проверим всех ботов в Киеве
cursor.execute('SELECT user_id, name, gender, city_normalized, is_bot, last_rotation_date FROM profiles WHERE city_normalized = ? AND is_bot = 1', (city_normalized,))
kyiv_bots = cursor.fetchall()

print(f'All bots in Kyiv:')
for bot in kyiv_bots:
    print(f'  ID: {bot[0]}, Name: {bot[1]}, Gender: {bot[2]}, City: {bot[3]}, IsBot: {bot[4]}, Rotation: {bot[5]}')

# Теперь проверим каждого бота по условиям SQL запроса
for bot in kyiv_bots:
    bot_id = bot[0]
    print(f'\n=== CHECKING BOT {bot_id} ===')
    
    # Условие 1: user_id != ?
    cond1 = bot_id != user_id
    print(f'1. user_id != {user_id}: {cond1}')
    
    # Условие 2: city_normalized = ?
    cond2 = bot[3] == city_normalized
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
    cond5 = (bot[4] == 0) or (bot[3] == city_normalized and bot[5] == '2026-01-29')
    print(f'5. Bot condition: {cond5} (is_bot={bot[4]}, city_normalized={bot[3]}, last_rotation_date={bot[5]})')
    
    all_conditions = cond1 and cond2 and cond3 and cond4 and cond5
    print(f'ALL CONDITIONS: {all_conditions}')
    
    if not all_conditions:
        print(f'*** BOT {bot_id} FAILS CONDITION CHECK! ***')

# Теперь выполним полный SQL запрос и посмотрим что он находит
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

cursor.execute(query, params)
results = cursor.fetchall()

print(f'\n=== SQL QUERY RESULTS ===')
print(f'Found {len(results)} profiles:')
for i, result in enumerate(results):
    print(f'  {i+1}: ID={result[1]}, Name={result[2]}, Gender={result[16]}, IsBot={result[19]}')

conn.close()
