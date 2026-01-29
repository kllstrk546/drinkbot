import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

# Проверим who_pays у киевских ботов
cursor.execute('SELECT DISTINCT who_pays FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv"')
bot_who_pays = cursor.fetchall()

print('Kyiv bots who_pays values:')
for value in bot_who_pays:
    print(f'  {value[0]}')

# Проверим mapping в коде
who_pays_mapping = {
    'i_treat': 'i_treat',
    'you_treat': 'someone_treats',
    'split': 'each_self',
    'any': None
}

print(f'\nMapping for split: {who_pays_mapping["split"]}')

conn.close()
