import sqlite3
from database.models import Database

db = Database()

user_id = 5483644714
city_normalized = 'Kyiv'

print(f'=== DEBUGGING FILTERING ISSUE ===')

# Получим профили как в коде
profiles = db.get_profiles_for_swiping_by_city_exact(user_id, city_normalized, limit=10)
print(f'Profiles from DB: {len(profiles)}')

for i, profile in enumerate(profiles):
    print(f'  Profile {i+1}: ID={profile["user_id"]}, Name={profile["name"]}, Gender={profile["gender"]}, IsBot={profile["is_bot"]}')

# Получим фильтры пользователя
user_filters = db.get_user_filters(user_id)
print(f'\nUser filters: {user_filters}')

# Применим фильтры как в коде
original_count = len(profiles)

if user_filters.get('gender') and user_filters.get('gender') != 'all':
    print(f'\nApplying gender filter: {user_filters.get("gender")}')
    profiles_before = len(profiles)
    profiles = [p for p in profiles if p.get('gender') == user_filters.get('gender')]
    print(f'Profiles after gender filter: {len(profiles)} (removed {profiles_before - len(profiles)})')

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
        profiles_before = len(profiles)
        profiles = [p for p in profiles if p.get('who_pays') == db_filter_value]
        print(f'Profiles after who_pays filter: {len(profiles)} (removed {profiles_before - len(profiles)})')

print(f'\nFinal result: {len(profiles)} profiles (started with {original_count})')

for i, profile in enumerate(profiles):
    print(f'  Final Profile {i+1}: ID={profile["user_id"]}, Name={profile["name"]}, Gender={profile["gender"]}, WhoPays={profile["who_pays"]}, IsBot={profile["is_bot"]}')

# Теперь проверим каждого бота отдельно
print(f'\n=== CHECKING INDIVIDUAL BOTS ===')

cursor = sqlite3.connect('drink_bot.db').cursor()
bot_ids = [-9999999, -8888888]

for bot_id in bot_ids:
    cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (bot_id,))
    bot = cursor.fetchone()
    
    if bot:
        print(f'\nBot {bot_id}:')
        print(f'  Name: {bot[2]}')
        print(f'  Gender: {bot[16]}')
        print(f'  Who Pays: {bot[9]}')
        print(f'  Is Bot: {bot[19]}')
        
        # Проверяем фильтры
        gender_match = (user_filters.get('gender') == 'all') or (bot[16] == user_filters.get('gender'))
        who_pays_match = (user_filters.get('who_pays') == 'any') or (bot[9] == who_pays_mapping.get(user_filters.get('who_pays')))
        
        print(f'  Gender filter match: {gender_match} (user wants: {user_filters.get("gender")})')
        print(f'  Who pays filter match: {who_pays_match} (user wants: {user_filters.get("who_pays")})')
        print(f'  Should be shown: {gender_match and who_pays_match}')
    else:
        print(f'\nBot {bot_id}: NOT FOUND')

cursor.close()
