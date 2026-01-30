import sqlite3

def check_cleanup():
    """Проверка результатов очистки"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CHECKING CLEANUP RESULTS:")
    print("=" * 50)
    
    # Проверяем количество реальных пользователей
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 0")
    real_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_bot = 1")
    bot_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM profiles")
    total_users = cursor.fetchone()[0]
    
    print(f"Real users: {real_users}")
    print(f"Bot users: {bot_users}")
    print(f"Total users: {total_users}")
    
    # Показываем оставшихся реальных пользователей
    cursor.execute("SELECT user_id, name, city FROM profiles WHERE is_bot = 0")
    remaining_real = cursor.fetchall()
    
    if remaining_real:
        print(f"Remaining real users: {len(remaining_real)}")
        for user_id, name, city in remaining_real:
            print(f"  ID: {user_id}, Name: {name}, City: {city}")
    else:
        print("No real users remaining - SUCCESS!")
    
    conn.close()

if __name__ == "__main__":
    check_cleanup()
