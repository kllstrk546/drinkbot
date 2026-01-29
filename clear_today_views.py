import sqlite3

def clear_today_views():
    """Очистить просмотры для тестовых пользователей"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    test_users = [547486189, 5483644714]
    
    print("CLEARING TODAY'S VIEWS FOR TEST USERS:")
    print("=" * 50)
    
    for user_id in test_users:
        # Проверяем сколько просмотров сегодня
        cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND view_date = DATE("now")', (user_id,))
        today_views = cursor.fetchone()[0]
        
        print(f"User {user_id}: {today_views} views today")
        
        # Удаляем все просмотры сегодня
        cursor.execute('DELETE FROM profile_views WHERE user_id = ? AND view_date = DATE("now")', (user_id,))
        deleted = cursor.rowcount
        
        print(f"  Deleted {deleted} views")
    
    conn.commit()
    
    # Проверяем результат
    print("\nAFTER CLEARING:")
    for user_id in test_users:
        cursor.execute('SELECT COUNT(*) FROM profile_views WHERE user_id = ? AND view_date = DATE("now")', (user_id,))
        remaining = cursor.fetchone()[0]
        print(f"User {user_id}: {remaining} views today")
    
    conn.close()
    print("\nViews cleared! Try searching again.")

if __name__ == "__main__":
    clear_today_views()
