import sqlite3
from database.models import Database

db = Database()

user_id = 547486189
city_normalized = 'Kyiv'

# Полностью повторим процесс из process_dating_city_input
print('=== DEBUGGING FULL PROCESS ===')

# Получим фильтры пользователя
user_filters = db.get_user_filters(user_id)
print(f'User filters: {user_filters}')

# Get profiles from specified city only (exact match) with filters
profiles = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)
print(f'Profiles with filters: {len(profiles)}')

# Also check profiles without filters to determine the reason
profiles_without_filters = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)
print(f'Profiles without filters: {len(profiles_without_filters)}')

# Apply filters manually for now (simplified version)
if user_filters.get('gender') and user_filters.get('gender') != 'all':
    print(f'Applying gender filter: {user_filters.get("gender")}')
    profiles = [p for p in profiles if p.get('gender') == user_filters.get('gender')]
    print(f'Profiles after gender filter: {len(profiles)}')

if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
    print(f'Applying who_pays filter: {user_filters.get("who_pays")}')
    who_pays_mapping = {
        'i_treat': 'i_treat',
        'you_treat': 'someone_treats',
        'split': 'each_self'
    }
    db_filter_value = who_pays_mapping.get(user_filters.get('who_pays'))
    if db_filter_value:
        profiles = [p for p in profiles if p.get('who_pays') == db_filter_value]
    print(f'Profiles after who_pays filter: {len(profiles)}')

print(f'\nFinal result:')
print(f'  profiles: {len(profiles)}')
print(f'  profiles_without_filters: {len(profiles_without_filters)}')

if profiles:
    print(f'  First profile:')
    profile = profiles[0]
    print(f'    ID: {profile["user_id"]}')
    print(f'    Name: {profile["name"]}')
    print(f'    Age: {profile["age"]}')
    print(f'    Gender: {profile["gender"]}')
    print(f'    Photo ID: {profile.get("photo_id", "None")}')
else:
    print('  No profiles found!')
    
    if profiles_without_filters:
        print('  But there are profiles without filters!')
    else:
        print('  And no profiles without filters either!')
