import sqlite3
from datetime import datetime

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Обновим дату ротации на сегодняшнюю
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('UPDATE profiles SET last_rotation_date = ? WHERE is_bot = 1', (today,))
conn.commit()

print(f'Updated rotation date to {today} for all bots')

# Проверим сколько ботов в Киеве
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = ?', (today,))
kyiv_bots_count = cursor.fetchone()[0]
print(f'Active bots in Kyiv: {kyiv_bots_count}')

# Проверим распределение по гендеру в Киеве
cursor.execute('SELECT gender, COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = ? GROUP BY gender', (today,))
kyiv_gender = cursor.fetchall()

print('Kyiv bots by gender:')
for gender, count in kyiv_gender:
    print(f'  {gender}: {count}')

# Общее количество активных ботов
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?', (today,))
total_active = cursor.fetchone()[0]
print(f'Total active bots: {total_active}')

# Распределение по городам (топ 10)
cursor.execute('''
    SELECT city_normalized, COUNT(*) 
    FROM profiles 
    WHERE is_bot = 1 AND last_rotation_date = ? 
    GROUP BY city_normalized 
    ORDER BY COUNT(*) DESC 
    LIMIT 10
''', (today,))

top_cities = cursor.fetchall()
print('\nTop 10 cities by bot count:')
for city, count in top_cities:
    print(f'  {city}: {count}')

conn.close()
