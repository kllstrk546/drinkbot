import sqlite3
from database.models import Database

db = Database()

# Протестируем функцию с нашими параметрами
user_id = 547486189
city_normalized = 'Kyiv'

profiles = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)

print(f'Found {len(profiles)} profiles for exact city search')

for i, profile in enumerate(profiles):
    print(f'  Profile {i+1}:')
    print(f'    ID: {profile["user_id"]}')
    print(f'    Name: {profile["name"]}')
    print(f'    Gender: {profile["gender"]}')
    print(f'    City: {profile["city"]}')
    print(f'    City Normalized: {profile["city_normalized"]}')
    print(f'    Is Bot: {profile["is_bot"]}')
    print(f'    Who Pays: {profile["who_pays"]}')
    print(f'    Last Rotation: {profile["last_rotation_date"]}')
    print()
