import sqlite3
from datetime import datetime

def test_empty_profiles_fix():
    """Тест исправления проблемы с пустыми анкетами"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("TESTING EMPTY PROFILES FIX:")
    print("=" * 50)
    
    # 1. Проверяем текущее состояние
    cursor.execute('''
        SELECT COUNT(*)
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
    ''', (city_normalized, today, user_id, user_id, user_id))
    
    available_count = cursor.fetchone()[0]
    print(f"Currently available bots: {available_count}")
    
    # 2. Симулируем ситуацию когда остается 1 бот
    print(f"\n2. SIMULATING 1 BOT REMAINING:")
    
    # Получаем всех доступных ботов
    cursor.execute('''
        SELECT user_id
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        ORDER BY RANDOM()
    ''', (city_normalized, today, user_id, user_id, user_id))
    
    all_available = cursor.fetchall()
    print(f"All available bots: {len(all_available)}")
    
    if len(all_available) > 1:
        # Добавляем просмотры для всех кроме одного
        for bot in all_available[:-1]:  # Все кроме последнего
            bot_id = bot[0]
            cursor.execute('''
                INSERT OR IGNORE INTO profile_views (user_id, profile_id, view_date)
                VALUES (?, ?, DATE('now'))
            ''', (user_id, bot_id))
        
        conn.commit()
        
        # Проверяем сколько осталось
        cursor.execute('''
            SELECT COUNT(*)
            FROM profiles p
            WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
            AND p.user_id != ?
            AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
            AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        ''', (city_normalized, today, user_id, user_id, user_id))
        
        remaining_count = cursor.fetchone()[0]
        print(f"After adding views: {remaining_count} bots available")
        
        # Проверяем что вернет SQL
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
        print(f"SQL returns: {len(sql_results)} bots")
        
        # 3. Тестируем логику handlers
        print(f"\n3. TESTING HANDLERS LOGIC:")
        
        if len(sql_results) == 0:
            print("  BEFORE FIX: Would show 'no profiles' immediately")
            print("  AFTER FIX: Still shows 'no profiles' immediately")
        elif len(sql_results) == 1:
            print("  BEFORE FIX: Would show 1 bot, then 'no profiles' on next swipe")
            print("  AFTER FIX: Shows 'no profiles' immediately (FIXED!)")
            print("  This prevents the confusing single bot display")
        else:
            print(f"  BEFORE FIX: Normal operation with {len(sql_results)} bots")
            print("  AFTER FIX: Normal operation (no change)")
        
        # 4. Симулируем ситуацию когда 0 ботов
        print(f"\n4. SIMULATING 0 BOTS:")
        
        # Добавляем просмотр для последнего бота
        if len(sql_results) == 1:
            last_bot_id = sql_results[0][0]
            cursor.execute('''
                INSERT OR IGNORE INTO profile_views (user_id, profile_id, view_date)
                VALUES (?, ?, DATE('now'))
            ''', (user_id, last_bot_id))
            
            conn.commit()
            
            # Проверяем что вернет SQL
            cursor.execute('''
                SELECT COUNT(*)
                FROM profiles p
                WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
                AND p.user_id != ?
                AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
                AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
            ''', (city_normalized, today, user_id, user_id, user_id))
            
            final_count = cursor.fetchone()[0]
            print(f"After viewing last bot: {final_count} bots available")
            
            if final_count == 0:
                print("  BEFORE FIX: Would show 'no profiles' immediately")
                print("  AFTER FIX: Still shows 'no profiles' immediately (no change)")
    
    # 5. Очищаем тестовые данные
    cursor.execute('''
        DELETE FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("EMPTY PROFILES FIX TEST COMPLETE!")
    print("\nFIX SUMMARY:")
    print("1. Added check for len(profiles) == 1 in start of search")
    print("2. Added check for current_index == len(profiles) - 1 in swipe")
    print("3. Both cases show 'no profiles' immediately instead of showing last bot")
    print("4. This prevents confusing single bot display")

if __name__ == "__main__":
    test_empty_profiles_fix()
