import sqlite3
from datetime import datetime

def debug_empty_profiles():
    """Диагностика проблемы с пустыми анкетами"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("DEBUGGING EMPTY PROFILES ISSUE:")
    print("=" * 60)
    print(f"User: {user_id}")
    print(f"City: {city_normalized}")
    print(f"Date: {today}")
    
    # 1. Проверяем сколько всего активных ботов в городе
    cursor.execute('''
        SELECT COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
    ''', (city_normalized, today))
    
    total_active = cursor.fetchone()[0]
    print(f"\n1. TOTAL ACTIVE BOTS IN {city_normalized}: {total_active}")
    
    # 2. Проверяем сколько ботов исключено по лайкам
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
    ''', (city_normalized, today, user_id))
    
    liked_bots = cursor.fetchone()[0]
    print(f"2. BOTS EXCLUDED BY LIKES: {liked_bots}")
    
    # 3. Проверяем сколько ботов исключено по просмотрам
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (city_normalized, today, user_id))
    
    viewed_bots = cursor.fetchone()[0]
    print(f"3. BOTS EXCLUDED BY VIEWS TODAY: {viewed_bots}")
    
    # 4. Проверяем сколько доступно ботов
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (city_normalized, today, user_id, user_id, user_id))
    
    available_bots = cursor.fetchone()[0]
    print(f"4. AVAILABLE BOTS: {available_bots}")
    
    # 5. Проверяем что возвращает SQL запрос
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.user_id != ? 
        AND p.city_normalized = ?
        AND dbo.city_normalized = ?
        AND dbo.date = DATE('now')
        AND p.user_id NOT IN (
            SELECT to_user_id FROM likes WHERE from_user_id = ?
        )
        AND p.user_id NOT IN (
            SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now')
        )
        AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
        ORDER BY dbo.order_index
        LIMIT 10
    ''', (user_id, city_normalized, city_normalized, user_id, user_id, city_normalized))
    
    sql_results = cursor.fetchall()
    print(f"\n5. SQL QUERY RETURNS: {len(sql_results)} bots")
    for i, bot in enumerate(sql_results):
        user_id_bot, name, gender = bot
        print(f"   {i}. {name} ({gender})")
    
    # 6. Проверяем profile_views детально
    cursor.execute('''
        SELECT profile_id, view_date
        FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
        ORDER BY view_date DESC
        LIMIT 10
    ''', (user_id,))
    
    views = cursor.fetchall()
    print(f"\n6. PROFILE_VIEWS TODAY ({len(views)}):")
    for profile_id, view_date in views:
        cursor.execute('SELECT name FROM profiles WHERE user_id = ?', (profile_id,))
        name = cursor.fetchone()[0]
        print(f"   {name} ({profile_id}) at {view_date}")
    
    # 7. Проверяем есть ли проблема с daily_bot_order
    cursor.execute('''
        SELECT COUNT(*)
        FROM daily_bot_order dbo
        JOIN profiles p ON dbo.bot_user_id = p.user_id
        WHERE dbo.city_normalized = ? AND dbo.date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))
    ''', (city_normalized, today, user_id, user_id, user_id, city_normalized))
    
    order_available = cursor.fetchone()[0]
    print(f"\n7. AVAILABLE IN DAILY_ORDER: {order_available}")
    
    # 8. Симулируем проблему
    print(f"\n8. PROBLEM SIMULATION:")
    print(f"   If user has viewed {viewed_bots} bots today")
    print(f"   And {total_active - viewed_bots - liked_bots - 1} bots remaining")
    print(f"   Then SQL should return 0 or 1 bots")
    
    expected_remaining = total_active - viewed_bots - liked_bots
    print(f"   Expected remaining: {expected_remaining}")
    print(f"   SQL actually returns: {len(sql_results)}")
    
    # 9. Проверяем что происходит в handlers
    print(f"\n9. HANDLERS LOGIC CHECK:")
    print(f"   If profiles = []:")
    print(f"   - Should show 'no profiles' message immediately")
    print(f"   If profiles = [1 bot]:")
    print(f"   - Shows bot, then on next swipe shows 'no profiles'")
    print(f"   - This is the problem!")
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("EMPTY PROFILES DEBUGGING COMPLETE!")
    print("\nPOSSIBLE SOLUTIONS:")
    print("1. Check if len(profiles) == 0 before showing first bot")
    print("2. Check if len(profiles) == 1 and handle differently")
    print("3. Clear profile_views when all profiles are viewed")
    print("4. Show 'no profiles' message immediately when empty")

if __name__ == "__main__":
    debug_empty_profiles()
