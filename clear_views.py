import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим viewed profiles для user_id = 1
cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = 1 AND view_date = DATE("now")')
viewed_count = cursor.fetchone()[0]
print(f'User 1 viewed profiles today: {viewed_count}')

# Очистим viewed profiles для user_id = 1
cursor.execute('DELETE FROM profile_views WHERE user_id = 1')
conn.commit()
print('Cleared viewed profiles for user 1')

conn.close()
