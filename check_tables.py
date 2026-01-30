import sqlite3

conn = sqlite3.connect('drink_bot.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("TABLES IN DATABASE:")
for table in tables:
    print(f"  {table[0]}")

conn.close()
