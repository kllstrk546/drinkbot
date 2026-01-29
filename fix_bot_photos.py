import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим есть ли у ботов photo_id
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND (photo_id IS NULL OR photo_id = "")')
no_photo_count = cursor.fetchone()[0]
print(f'Bots without photo_id: {no_photo_count}')

# Проверим сколько ботов всего
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1')
total_bots = cursor.fetchone()[0]
print(f'Total bots: {total_bots}')

# Дадим всем ботам временный photo_id
temp_photo_id = 'AgACAgIAAxkDAAIBOGf6T7X8Y7x9v2w3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9'
cursor.execute('UPDATE profiles SET photo_id = ? WHERE is_bot = 1 AND (photo_id IS NULL OR photo_id = "")', (temp_photo_id,))
conn.commit()

print('Updated all bots with temporary photo_id')

conn.close()
