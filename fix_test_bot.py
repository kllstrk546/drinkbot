import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Обновим gender на female
cursor.execute('UPDATE profiles SET gender = ? WHERE user_id = ?', ('female', -9999999))
conn.commit()
print('Updated bot gender to female')

# Проверим результат
cursor.execute('SELECT user_id, name, age, gender, city, city_normalized, favorite_drink, photo_id, who_pays, is_bot, last_rotation_date FROM profiles WHERE user_id = -9999999')
bot = cursor.fetchone()

print(f'\nFinal test bot verification:')
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

# Теперь проверим найдет ли его запрос
print('\nTesting search query:')

user_id = 547486189
conditions = ["p.user_id != ?", "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)"]
params = [user_id, user_id]

conditions.append("p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))")
params.append(user_id)

all_cities = ['Kyiv', 'Kharkiv', 'Odesa', 'Lviv', 'Dnipro']
city_placeholders = ','.join(['?' for _ in all_cities])
conditions.append(f"p.city_normalized IN ({city_placeholders})")
params.extend(all_cities)

conditions.append("(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))")
params.append('Kyiv')

conditions.append("p.gender = ?")
params.append('female')

conditions.append("p.who_pays = ?")
params.append('each_self')

query = f'''
    SELECT p.* FROM profiles p
    WHERE {' AND '.join(conditions)}
    ORDER BY RANDOM()
    LIMIT 10
'''

cursor.execute(query, params)
results = cursor.fetchall()

print(f'Query found {len(results)} profiles')

for i, result in enumerate(results):
    print(f'  Profile {i+1}: ID={result[1]}, Name={result[2]}, Gender={result[16]}, City={result[6]}, IsBot={result[19]}, WhoPays={result[9]}')

conn.close()
