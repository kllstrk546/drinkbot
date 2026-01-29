import sqlite3
from datetime import datetime

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

today = datetime.now().strftime('%Y-%m-%d')

# Обновим дату ротации для всех ботов в Киеве
cursor.execute('UPDATE profiles SET last_rotation_date = ? WHERE is_bot = 1 AND city_normalized = "Kyiv"', (today,))
conn.commit()

print(f'Updated rotation date to {today} for Kyiv bots')

# Проверим результат
cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" AND last_rotation_date = ?', (today,))
updated_count = cursor.fetchone()[0]

print(f'Kyiv bots with today rotation: {updated_count}')

# Проверим поиск
user_id = 5483644714
cursor.execute('''
    SELECT COUNT(*) FROM profiles 
    WHERE user_id != ? 
    AND city_normalized = ?
    AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
    AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
''', (user_id, 'Kyiv', user_id, user_id, 'Kyiv'))

found_count = cursor.fetchone()[0]
print(f'Will find {found_count} profiles in search now')

# Очистим просмотры для пользователя
cursor.execute('DELETE FROM profile_views WHERE user_id = ?', (user_id,))
conn.commit()

print(f'Cleared views for user {user_id}')

conn.close()
