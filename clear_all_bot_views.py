import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Очистим просмотры обоих ботов
bot_ids = [-9999999, -8888888]
user_id = 5483644714

for bot_id in bot_ids:
    cursor.execute('DELETE FROM profile_views WHERE user_id = ? AND profile_id = ?', (user_id, bot_id))
    print(f'Deleted view for bot {bot_id}')

conn.commit()

# Проверим результат
for bot_id in bot_ids:
    cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND profile_id = ? AND view_date = DATE("now")', (user_id, bot_id))
    views_count = cursor.fetchone()[0]
    print(f'Bot {bot_id} views count: {views_count}')

print('All bot views cleared!')

# Теперь проверим SQL запрос снова
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

params = (user_id, 'Kyiv', user_id, user_id, 'Kyiv', 10)

cursor.execute(query, params)
results = cursor.fetchall()

print(f'\nSQL Query now finds {len(results)} profiles:')
for i, result in enumerate(results):
    print(f'  {i+1}: ID={result[1]}, Name={result[2]}, Gender={result[16]}, IsBot={result[19]}')

conn.close()
