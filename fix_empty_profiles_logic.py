import sqlite3
from datetime import datetime

def fix_empty_profiles_logic():
    """Исправляем логику пустых анкет"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("FIXING EMPTY PROFILES LOGIC:")
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
    
    # 2. Симулируем ситуацию когда почти все просмотрены
    print(f"\n2. SIMULATING NEARLY EMPTY STATE:")
    
    # Добавляем временные просмотры чтобы симулировать
    cursor.execute('''
        SELECT user_id
        FROM profiles p
        WHERE p.is_bot = 1 AND p.city_normalized = ? AND p.last_rotation_date = ?
        AND p.user_id != ?
        AND p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        ORDER BY RANDOM()
        LIMIT ?
    ''', (city_normalized, today, user_id, user_id, user_id, available_count - 1))
    
    remaining_bots = cursor.fetchall()
    
    if len(remaining_bots) > 0:
        # Добавляем просмотры для всех кроме одного
        for bot in remaining_bots[:-1]:  # Все кроме последнего
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
        
        final_available = cursor.fetchone()[0]
        print(f"After adding views: {final_available} bots available")
        
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
        
        final_results = cursor.fetchall()
        print(f"SQL returns: {len(final_results)} bots")
        for i, bot in enumerate(final_results):
            user_id_bot, name, gender = bot
            print(f"  {i}. {name} ({gender})")
        
        # 3. Тестируем логику которая должна быть в handlers
        print(f"\n3. TESTING HANDLERS LOGIC:")
        
        if len(final_results) == 0:
            print("  CORRECT: No profiles - should show 'no profiles' message immediately")
        elif len(final_results) == 1:
            print("  PROBLEM: 1 profile - will show bot then 'no profiles' on next swipe")
            print("  SOLUTION: Check if this is last profile and show 'no profiles' instead")
        else:
            print(f"  OK: {len(final_results)} profiles - normal operation")
    
    # 4. Очищаем временные просмотры
    cursor.execute('''
        DELETE FROM profile_views 
        WHERE user_id = ? AND view_date = DATE('now')
        AND profile_id IN (
            SELECT user_id FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ? AND last_rotation_date = ?
        )
    ''', (user_id, city_normalized, today))
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("EMPTY PROFILES LOGIC ANALYSIS COMPLETE!")
    print("\nSOLUTION NEEDED:")
    print("1. In handlers/start.py, check if len(profiles) == 0")
    print("2. If 0, show 'no profiles' message immediately")
    print("3. Don't show the last bot if it will cause confusion")
    print("4. Consider clearing profile_views when all are viewed")

if __name__ == "__main__":
    fix_empty_profiles_logic()
