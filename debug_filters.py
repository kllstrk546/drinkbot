import sqlite3
from database.models import Database

db = Database()

user_id = 547486189
city_normalized = 'Kyiv'

# Получим фильтры пользователя
user_filters = db.get_user_filters(user_id)
print(f'User filters: {user_filters}')

# Получим профили
profiles = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)
print(f'Found {len(profiles)} profiles before filtering')

for i, profile in enumerate(profiles):
    print(f'  Profile {i+1} before filtering:')
    print(f'    ID: {profile["user_id"]}')
    print(f'    Gender: {profile["gender"]}')
    print(f'    Who Pays: {profile["who_pays"]}')

# Применим ручную фильтрацию как в коде
if user_filters.get('gender') and user_filters.get('gender') != 'all':
    print(f'\nApplying gender filter: {user_filters.get("gender")}')
    profiles = [p for p in profiles if p.get('gender') == user_filters.get('gender')]
    print(f'Profiles after gender filter: {len(profiles)}')

if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
    print(f'\nApplying who_pays filter: {user_filters.get("who_pays")}')
    who_pays_mapping = {
        'i_treat': 'i_treat',
        'you_treat': 'someone_treats',
        'split': 'each_self'
    }
    db_filter_value = who_pays_mapping.get(user_filters.get('who_pays'))
    print(f'DB filter value: {db_filter_value}')
    if db_filter_value:
        profiles = [p for p in profiles if p.get('who_pays') == db_filter_value]
    print(f'Profiles after who_pays filter: {len(profiles)}')

print(f'\nFinal profiles after filtering: {len(profiles)}')

for i, profile in enumerate(profiles):
    print(f'  Profile {i+1} after filtering:')
    print(f'    ID: {profile["user_id"]}')
    print(f'    Gender: {profile["gender"]}')
    print(f'    Who Pays: {profile["who_pays"]}')
