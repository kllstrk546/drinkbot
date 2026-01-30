import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Получим правильные индексы колонок
cursor.execute('PRAGMA table_info(profiles)')
columns = cursor.fetchall()

print('Column indices:')
for i, col in enumerate(columns):
    print(f'  {i}: {col[1]}')

# Удалим тестового бота
cursor.execute('DELETE FROM profiles WHERE user_id = -9999999')
conn.commit()

# Создадим бота с правильными индексами
cursor.execute('''
    INSERT INTO profiles (
        user_id, username, name, age, gender, city, city_display,
        city_normalized, favorite_drink, photo_id, who_pays, language,
        is_bot, bot_photo_path, last_rotation_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    -9999999,  # user_id
    'test_bot_kyiv',  # username
    'Анна',  # name
    22,  # age
    'female',  # gender
    'Киев',  # city
    'Киев',  # city_display
    'Kyiv',  # city_normalized
    'Коктейль',  # favorite_drink
    'AgACAgIAAxkDAAIBOGf6T7X8Y7x9v2w3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9',  # photo_id
    'each_self',  # who_pays
    'ru',  # language
    1,  # is_bot
    'assets/bots/female/test.jpg',  # bot_photo_path
    '2026-01-29'  # last_rotation_date
))

conn.commit()
print('Created test bot with correct column order')

# Проверим результат
cursor.execute('SELECT user_id, name, age, gender, city, city_normalized, favorite_drink, photo_id, who_pays, is_bot, last_rotation_date FROM profiles WHERE user_id = -9999999')
bot = cursor.fetchone()

print(f'\nTest bot verification:')
print(f'  user_id: {bot[0]}')
print(f'  name: {bot[1]}')
print(f'  age: {bot[2]}')
print(f'  gender: {bot[3]}')
print(f'  city: {bot[4]}')
print(f'  city_normalized: {bot[5]}')
print(f'  favorite_drink: {bot[6]}')
print(f'  photo_id: {bot[7]}')
print(f'  who_pays: {bot[8]}')
print(f'  is_bot: {bot[9]}')
print(f'  last_rotation_date: {bot[10]}')

conn.close()
