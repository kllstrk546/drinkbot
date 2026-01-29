import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим фильтры для user_id = 1
cursor.execute('SELECT filter_gender, filter_who_pays FROM profiles WHERE user_id = 1')
filters = cursor.fetchone()

if filters:
    print(f'User 1 filters: gender={filters[0]}, who_pays={filters[1]}')
else:
    print('No filters found for user 1')

# Проверим всех пользователей
cursor.execute('SELECT user_id, filter_gender, filter_who_pays FROM profiles WHERE user_id > 0 LIMIT 5')
all_filters = cursor.fetchall()

print('\nAll users filters:')
for user_filter in all_filters:
    print(f'User {user_filter[0]}: gender={user_filter[1]}, who_pays={user_filter[2]}')

conn.close()
