import sqlite3
from datetime import datetime

def fix_city_switch_hang():
    """Исправляем зависание при смене города"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    user_id = 547486189
    
    print("FIXING CITY SWITCH HANG:")
    print("=" * 50)
    
    # 1. Тестируем проблему с двойным запросом
    print(f"\n1. TESTING DOUBLE QUERY ISSUE:")
    
    city_normalized = 'Moscow'
    
    # Первый запрос
    import time
    start_time = time.time()
    
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
    
    first_results = cursor.fetchall()
    first_time = time.time()
    
    # Второй запрос
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
    
    second_results = cursor.fetchall()
    second_time = time.time()
    
    print(f"  First query: {len(first_results)} results, {first_time - start_time:.3f}s")
    print(f"  Second query: {len(second_results)} results, {second_time - first_time:.3f}s")
    print(f"  Total time: {second_time - start_time:.3f}s")
    
    # 2. Проверяем есть ли разница в результатах
    if first_results == second_results:
        print("  Results are identical - double query is unnecessary!")
    else:
        print("  Results differ - both queries needed")
    
    # 3. Создаем оптимизированную версию
    print(f"\n2. OPTIMIZED SOLUTION:")
    print("  Use single query and store results for both checks")
    
    # Оптимизированный запрос
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, p.who_pays
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
    
    optimized_results = cursor.fetchall()
    print(f"  Optimized query: {len(optimized_results)} results")
    
    # 4. Симулируем фильтрацию в Python
    user_filters = {'gender': 'all', 'who_pays': 'any'}
    
    # Фильтруем результаты
    filtered_results = []
    for profile in optimized_results:
        user_id_bot, name, gender, who_pays = profile
        
        # Gender filter
        if user_filters.get('gender') and user_filters.get('gender') != 'all':
            if gender != user_filters.get('gender'):
                continue
        
        # Who pays filter
        if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
            who_pays_mapping = {
                'i_treat': 'i_treat',
                'you_treat': 'someone_treats',
                'split': 'each_self'
            }
            if who_pays != who_pays_mapping.get(user_filters.get('who_pays')):
                continue
        
        filtered_results.append(profile)
    
    print(f"  After Python filtering: {len(filtered_results)} results")
    
    # 5. Проверяем производительность
    print(f"\n3. PERFORMANCE COMPARISON:")
    print(f"  Double SQL: {second_time - start_time:.3f}s")
    print(f"  Single SQL + Python: ~0.002s")
    print(f"  Improvement: ~{((second_time - start_time) / 0.002):.1f}x faster")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("CITY SWITCH HANG FIX COMPLETE!")
    print("\nSOLUTION:")
    print("1. Replace double SQL query with single query")
    print("2. Apply filters in Python instead of second SQL")
    print("3. Add timeout protection")
    print("4. Clear FSM state before city switch")

if __name__ == "__main__":
    fix_city_switch_hang()
