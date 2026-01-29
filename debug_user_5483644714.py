import sqlite3
from database.models import Database

db = Database()

user_id = 5483644714
city_normalized = 'Kyiv'

print(f'=== DEBUGGING USER {user_id} ===')

# Получим фильтры пользователя
user_filters = db.get_user_filters(user_id)
print(f'User filters: {user_filters}')

# Get profiles from specified city only (exact match) with filters
profiles = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)
print(f'Profiles found: {len(profiles)}')

for i, profile in enumerate(profiles):
    print(f'  Profile {i+1}:')
    print(f'    ID: {profile["user_id"]}')
    print(f'    Name: {profile["name"]}')
    print(f'    Age: {profile["age"]}')
    print(f'    Gender: {profile["gender"]}')
    print(f'    City: {profile["city"]}')
    print(f'    City Normalized: {profile["city_normalized"]}')
    print(f'    Is Bot: {profile["is_bot"]}')
    print(f'    Who Pays: {profile["who_pays"]}')
    print(f'    Last Rotation: {profile["last_rotation_date"]}')
    print(f'    Photo ID: {profile.get("photo_id", "None")}')
    print()

# Проверим вручную нашего бота
bot_id = -9999999
cursor = sqlite3.connect('drink_bot.db').cursor()
cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (bot_id,))
bot_data = cursor.fetchone()

if bot_data:
    print(f'Bot {bot_id} exists in database:')
    print(f'  user_id: {bot_data[1]}')
    print(f'  name: {bot_data[2]}')
    print(f'  age: {bot_data[3]}')
    print(f'  gender: {bot_data[16]}')
    print(f'  city: {bot_data[4]}')
    print(f'  city_normalized: {bot_data[6]}')
    print(f'  is_bot: {bot_data[19]}')
    print(f'  who_pays: {bot_data[9]}')
    print(f'  last_rotation_date: {bot_data[21]}')
    print(f'  photo_id: {bot_data[8]}')
else:
    print(f'Bot {bot_id} NOT found in database!')

# Проверим проходит ли бот все условия SQL запроса
print(f'\n=== CHECKING BOT CONDITIONS ===')
print(f'Bot user_id != {user_id}: {bot_id != user_id}')
print(f'Bot city_normalized == Kyiv: {bot_data[6] == "Kyiv" if bot_data else "N/A"}')
print(f'Bot is_bot == 1: {bot_data[19] == 1 if bot_data else "N/A"}')
print(f'Bot last_rotation_date == today: {bot_data[21] == "2026-01-29" if bot_data else "N/A"}')

cursor.close()
