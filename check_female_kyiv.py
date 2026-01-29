import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим who_pays у женских ботов в Киеве
cursor.execute('SELECT who_pays, COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now") AND gender = "female" GROUP BY who_pays')
female_kyiv = cursor.fetchall()

print('Female Kyiv bots by who_pays:')
for who_pays, count in female_kyiv:
    print(f'  {who_pays}: {count}')

# Посмотрим на всех женских ботов в Киеве
cursor.execute('SELECT name, age, who_pays FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now") AND gender = "female"')
all_female = cursor.fetchall()

print('\nAll female Kyiv bots:')
for bot in all_female:
    print(f'  {bot[0]}, {bot[1]}, who_pays={bot[2]}')

conn.close()
