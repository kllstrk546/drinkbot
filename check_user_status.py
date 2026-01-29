import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим лайки пользователя 547486189
cursor.execute('SELECT to_user_id FROM likes WHERE from_user_id = 547486189')
user_likes = cursor.fetchall()

print(f'User 547486189 likes: {[like[0] for like in user_likes]}')

# Проверим viewed profiles пользователя 547486189
cursor.execute('SELECT profile_id FROM profile_views WHERE user_id = 547486189 AND view_date = DATE("now")')
user_views = cursor.fetchall()

print(f'User 547486189 viewed today: {[view[0] for view in user_views]}')

# Проверим есть ли наш бот в лайках или просмотрах
bot_id = -9999999
liked_bot = bot_id in [like[0] for like in user_likes]
viewed_bot = bot_id in [view[0] for view in user_views]

print(f'Bot {bot_id} liked by user 547486189: {liked_bot}')
print(f'Bot {bot_id} viewed by user 547486189: {viewed_bot}')

# Очистим лайки и просмотры для пользователя 547486189
cursor.execute('DELETE FROM likes WHERE from_user_id = 547486189')
cursor.execute('DELETE FROM profile_views WHERE user_id = 547486189')
conn.commit()

print('Cleared likes and views for user 547486189')

conn.close()
