import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим сколько ботов в Киеве с сегодняшней датой
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = "2026-01-29"')
kyiv_bots = cursor.fetchone()[0]

print(f'Bots in Kyiv with today rotation: {kyiv_bots}')

# Проверим сколько всего ботов в Киеве
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv"')
total_kyiv_bots = cursor.fetchone()[0]

print(f'Total bots in Kyiv: {total_kyiv_bots}')

# Проверим даты ротации у киевских ботов
cursor.execute('SELECT DISTINCT last_rotation_date FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv"')
dates = cursor.fetchall()

print(f'Rotation dates for Kyiv bots: {[d[0] for d in dates]}')

# Проверим сколько профилей найдется в поиске для пользователя
user_id = 5483644714
cursor.execute('''
    SELECT COUNT(*) FROM profiles 
    WHERE user_id != ? 
    AND city_normalized = ?
    AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
    AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
''', (user_id, 'Kyiv', user_id, user_id, 'Kyiv'))

found_count = cursor.fetchone()[0]
print(f'Will find {found_count} profiles in search')

# Проверим конкретные боты в Киеве
cursor.execute('SELECT user_id, name, age, gender, last_rotation_date FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" LIMIT 5')
bots_sample = cursor.fetchall()

print('Sample bots in Kyiv:')
for bot in bots_sample:
    print(f'  ID: {bot[0]}, Name: {bot[1]}, Age: {bot[2]}, Gender: {bot[3]}, Rotation: {bot[4]}')

conn.close()
