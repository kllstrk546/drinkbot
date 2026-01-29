import sqlite3

def test_sql_query():
    """Тестируем SQL запрос напрямую"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    user_id = 547486189
    city_normalized = 'Kyiv'
    
    print("TESTING SQL QUERY DIRECTLY:")
    print("=" * 40)
    
    # 1. Базовый запрос без фильтров
    cursor.execute('''
        SELECT user_id, name, gender, photo_id
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        ORDER BY RANDOM()
        LIMIT 10
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    base_results = cursor.fetchall()
    print(f"Base query results: {len(base_results)}")
    
    for i, result in enumerate(base_results):
        user_id_bot, name, gender, photo_id = result
        print(f"  {i+1}. {name} ({gender}) - {photo_id[:30] if photo_id else 'NO PHOTO'}...")
    
    # 2. Запрос с фильтрами
    cursor.execute('''
        SELECT user_id, name, gender, photo_id
        FROM profiles 
        WHERE user_id != ? 
        AND city_normalized = ?
        AND user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)
        AND user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))
        AND (is_bot = 0 OR (city_normalized = ? AND last_rotation_date = DATE('now')))
        AND gender = 'male'
        AND who_pays = 'i_treat'
        ORDER BY RANDOM()
        LIMIT 10
    ''', (user_id, city_normalized, user_id, user_id, city_normalized))
    
    filtered_results = cursor.fetchall()
    print(f"\nFiltered query results: {len(filtered_results)}")
    
    for i, result in enumerate(filtered_results):
        user_id_bot, name, gender, photo_id = result
        print(f"  {i+1}. {name} ({gender}) - {photo_id[:30] if photo_id else 'NO PHOTO'}...")
    
    # 3. Проверяем who_pays распределение
    cursor.execute('''
        SELECT who_pays, COUNT(*) 
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = ? AND gender = 'male'
        GROUP BY who_pays
        ORDER BY who_pays
    ''', (city_normalized,))
    
    who_pays_dist = cursor.fetchall()
    print(f"\nMale bots who_pays distribution:")
    for wp, count in who_pays_dist:
        print(f"  {wp}: {count}")
    
    conn.close()

if __name__ == "__main__":
    test_sql_query()
