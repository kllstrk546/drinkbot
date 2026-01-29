import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим кого лайкал пользователь 547486189
cursor.execute('''
    SELECT p.user_id, p.name, p.age, p.gender, p.city, p.city_normalized, p.is_bot, p.who_pays
    FROM profiles p
    WHERE p.user_id IN (SELECT to_user_id FROM likes WHERE from_user_id = 547486189)
''')
liked_profiles = cursor.fetchall()

print('Profiles liked by user 547486189:')
for profile in liked_profiles:
    print(f'  ID={profile[0]}, Name={profile[1]}, Age={profile[2]}, Gender={profile[3]}, City={profile[4]}, IsBot={profile[6]}, WhoPays={profile[7]}')

# Теперь проверим всех доступных женских ботов в Киеве
cursor.execute('''
    SELECT p.user_id, p.name, p.age, p.gender, p.city, p.city_normalized, p.is_bot, p.who_pays
    FROM profiles p
    WHERE p.is_bot = 1 
    AND p.city_normalized = 'Kyiv' 
    AND p.last_rotation_date = DATE('now')
    AND p.gender = 'female'
    AND p.who_pays = 'each_self'
''')
available_female_bots = cursor.fetchall()

print('\nAvailable female bots in Kyiv with each_self:')
for bot in available_female_bots:
    print(f'  ID={bot[0]}, Name={bot[1]}, Age={bot[2]}, Gender={bot[3]}, City={bot[4]}, IsBot={bot[6]}, WhoPays={bot[7]}')

# Проверим пересечения
liked_ids = [profile[0] for profile in liked_profiles]
available_ids = [bot[0] for bot in available_female_bots]

not_liked_bots = [bot for bot in available_female_bots if bot[0] not in liked_ids]

print(f'\nNot liked female bots: {len(not_liked_bots)}')
for bot in not_liked_bots:
    print(f'  ID={bot[0]}, Name={bot[1]}, Age={bot[2]}, WhoPays={bot[7]}')

conn.close()
