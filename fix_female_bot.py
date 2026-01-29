import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Обновим одну женскую бот в Киеве чтобы у нее было who_pays = each_self
cursor.execute('''
    UPDATE profiles 
    SET who_pays = 'each_self' 
    WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND gender = 'female' AND last_rotation_date = DATE('now')
    AND rowid = (SELECT rowid FROM profiles WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND gender = 'female' AND last_rotation_date = DATE('now') LIMIT 1)
''')
conn.commit()

print('Updated 1 female Kyiv bot to have who_pays = each_self')

# Проверим результат
cursor.execute('SELECT who_pays, COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = DATE("now") AND gender = "female" GROUP BY who_pays')
female_kyiv = cursor.fetchall()

print('Female Kyiv bots by who_pays after update:')
for who_pays, count in female_kyiv:
    print(f'  {who_pays}: {count}')

conn.close()
