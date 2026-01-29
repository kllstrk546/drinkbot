import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Удалим всех ботов и создадим заново с правильной структурой
print('Deleting all bots...')
cursor.execute('DELETE FROM profiles WHERE is_bot = 1')
conn.commit()

# Создадим одного тестового бота в Киеве с правильными данными
test_bot = {
    'user_id': -9999999,
    'username': 'test_bot_kyiv',
    'name': 'Анна',
    'age': 22,
    'gender': 'female',
    'city': 'Киев',
    'city_display': 'Киев',
    'city_normalized': 'Kyiv',
    'favorite_drink': 'Коктейль',
    'who_pays': 'each_self',
    'language': 'ru',
    'is_bot': 1,
    'bot_photo_path': 'assets/bots/female/test.jpg',
    'last_rotation_date': '2026-01-29',
    'photo_id': 'AgACAgIAAxkDAAIBOGf6T7X8Y7x9v2w3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9'
}

cursor.execute('''
    INSERT INTO profiles (
        user_id, username, name, age, gender, city, city_display,
        city_normalized, favorite_drink, who_pays, language,
        is_bot, bot_photo_path, last_rotation_date, photo_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    test_bot['user_id'], test_bot['username'], test_bot['name'],
    test_bot['age'], test_bot['gender'], test_bot['city'],
    test_bot['city_display'], test_bot['city_normalized'],
    test_bot['favorite_drink'], test_bot['who_pays'],
    test_bot['language'], test_bot['is_bot'], test_bot['bot_photo_path'],
    test_bot['last_rotation_date'], test_bot['photo_id']
))

conn.commit()
print('Created test bot with correct data structure')

# Проверим что получилось
cursor.execute('SELECT * FROM profiles WHERE user_id = -9999999')
bot = cursor.fetchone()

print(f'\nTest bot data:')
print(f'  user_id: {bot[1]}')
print(f'  name: {bot[2]}')
print(f'  age: {bot[3]}')
print(f'  gender: {bot[5]}')
print(f'  city: {bot[4]}')
print(f'  city_normalized: {bot[6]}')
print(f'  favorite_drink: {bot[7]}')
print(f'  who_pays: {bot[9]}')
print(f'  is_bot: {bot[13]}')
print(f'  last_rotation_date: {bot[16]}')
print(f'  photo_id: {bot[8]}')

conn.close()
