import sqlite3

def check_views_detailed():
    """Детальная проверка просмотров"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 547486189
    
    print("DETAILED VIEWS CHECK:")
    print("=" * 40)
    
    # Все просмотры пользователя
    cursor.execute('SELECT profile_id, view_date FROM profile_views WHERE user_id = ? ORDER BY view_date DESC LIMIT 10', (user_id,))
    all_views = cursor.fetchall()
    
    print(f"User {user_id} recent views:")
    for profile_id, view_date in all_views:
        print(f"  {profile_id} - {view_date}")
    
    # Просмотры сегодня
    cursor.execute('SELECT profile_id, view_date FROM profile_views WHERE user_id = ? AND view_date = DATE("now")', (user_id,))
    today_views = cursor.fetchall()
    
    print(f"\nToday's views ({len(today_views)}):")
    for profile_id, view_date in today_views:
        print(f"  {profile_id} - {view_date}")
    
    # Все боты в Киеве
    cursor.execute('SELECT user_id, name FROM profiles WHERE is_bot = 1 AND city_normalized = "Kyiv" ORDER BY user_id')
    kyiv_bots = cursor.fetchall()
    
    print(f"\nKyiv bots ({len(kyiv_bots)}):")
    for bot_id, name in kyiv_bots[:5]:
        print(f"  {bot_id} - {name}")
    
    # Пересечение
    viewed_bot_ids = [v[0] for v in today_views]
    kyiv_bot_ids = [b[0] for b in kyiv_bots]
    
    intersection = set(viewed_bot_ids) & set(kyiv_bot_ids)
    
    print(f"\nIntersection (viewed Kyiv bots today): {len(intersection)}")
    for bot_id in intersection:
        print(f"  {bot_id}")
    
    conn.close()

if __name__ == "__main__":
    check_views_detailed()
