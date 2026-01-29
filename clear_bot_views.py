import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Удалим просмотры нашего бота
bot_id = -9999999
user_id = 5483644714

cursor.execute('DELETE FROM profile_views WHERE user_id = ? AND profile_id = ?', (user_id, bot_id))
conn.commit()

print(f'Deleted profile_views for user {user_id} viewing bot {bot_id}')

# Проверим результат
cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND profile_id = ? AND view_date = DATE("now")', (user_id, bot_id))
views_count = cursor.fetchone()[0]

print(f'Views count now: {views_count}')

# Очистим вообще все просмотры для пользователя на всякий случай
cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
conn.commit()

print(f'Cleared ALL profile_views for user {user_id}')

conn.close()
