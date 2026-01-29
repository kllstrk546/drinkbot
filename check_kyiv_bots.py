import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим распределение ботов в Киеве по гендеру
cursor.execute('SELECT gender, COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now") GROUP BY gender')
kyiv_bots = cursor.fetchall()

print('Kyiv bots by gender:')
for gender, count in kyiv_bots:
    print(f'  {gender}: {count}')

# Проверим сколько всего ботов в Киеве
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now")')
total_kyiv = cursor.fetchone()[0]
print(f'Total Kyiv bots: {total_kyiv}')

# Проверим сколько женских ботов в Киеве с who_pays = each_self
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now") AND gender = "female" AND who_pays = "each_self"')
female_kyiv_each_self = cursor.fetchone()[0]
print(f'Female Kyiv bots with each_self: {female_kyiv_each_self}')

conn.close()
