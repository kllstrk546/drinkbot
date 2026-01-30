import sqlite3

def check_duplicates():
    """Проверка дубликатов в daily_bot_order"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    print("CHECKING DUPLICATES IN DAILY_BOT_ORDER:")
    print("=" * 50)
    
    today = '2026-01-30'
    
    # 1. Проверяем дубликаты bot_user_id
    print(f"\n1. CHECKING DUPLICATE bot_user_id:")
    
    cursor.execute('''
        SELECT bot_user_id, COUNT(*) as count
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY bot_user_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    ''', (today,))
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"   FOUND {len(duplicates)} DUPLICATES:")
        for bot_id, count in duplicates:
            print(f"     Bot {bot_id}: {count} entries")
    else:
        print("   No duplicates found in bot_user_id")
    
    # 2. Проверяем дубликаты по городам
    print(f"\n2. CHECKING DUPLICATES BY CITY:")
    
    cursor.execute('''
        SELECT city_normalized, bot_user_id, COUNT(*) as count
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized, bot_user_id
        HAVING COUNT(*) > 1
        ORDER BY city_normalized, count DESC
    ''', (today,))
    
    city_duplicates = cursor.fetchall()
    
    if city_duplicates:
        print(f"   FOUND {len(city_duplicates)} CITY DUPLICATES:")
        for city, bot_id, count in city_duplicates:
            print(f"     {city}: Bot {bot_id} ({count} entries)")
    else:
        print("   No duplicates found by city")
    
    # 3. Проверяем общее количество записей
    print(f"\n3. TOTAL RECORDS CHECK:")
    
    cursor.execute('''
        SELECT COUNT(*) FROM daily_bot_order WHERE date = ?
    ''', (today,))
    
    total_records = cursor.fetchone()[0]
    print(f"   Total records: {total_records}")
    
    cursor.execute('''
        SELECT COUNT(DISTINCT bot_user_id) FROM daily_bot_order WHERE date = ?
    ''', (today,))
    
    unique_bots = cursor.fetchone()[0]
    print(f"   Unique bots: {unique_bots}")
    
    if total_records != unique_bots:
        print(f"   WARNING: {total_records - unique_bots} duplicate entries!")
    else:
        print(f"   OK: No duplicates detected")
    
    # 4. Проверяем порядок индексов
    print(f"\n4. ORDER INDEX CHECK:")
    
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count,
               MIN(order_index) as min_idx,
               MAX(order_index) as max_idx
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized
        ORDER BY city_normalized
    ''', (today,))
    
    city_orders = cursor.fetchall()
    
    print(f"   City order indices:")
    for city, count, min_idx, max_idx in city_orders:
        expected_max = count - 1
        status = "OK" if max_idx == expected_max else f"ERROR (expected {expected_max})"
        print(f"     {city}: {count} entries, indices {min_idx}-{max_idx} ({status})")
    
    # 5. Проверяем конкретные боты из лога
    print(f"\n5. CHECKING LOG PROFILES:")
    
    log_profiles = [-62932917, -56330984]  # Из лога
    
    for profile_id in log_profiles:
        cursor.execute('''
            SELECT city_normalized, order_index FROM daily_bot_order 
            WHERE date = ? AND bot_user_id = ?
        ''', (today, profile_id))
        
        result = cursor.fetchone()
        if result:
            city, order_idx = result
            print(f"   Profile {profile_id}: {city}, index {order_idx}")
        else:
            print(f"   Profile {profile_id}: NOT FOUND")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("DUPLICATE CHECK COMPLETE!")
    
    if duplicates or city_duplicates:
        print("\nDUPLICATES FOUND - NEED TO FIX!")
    else:
        print("\nNO DUPLICATES - ISSUE ELSEWHERE")

if __name__ == "__main__":
    check_duplicates()
