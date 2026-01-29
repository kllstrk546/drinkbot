import sqlite3
from datetime import datetime

def comprehensive_diagnosis():
    """Комплексная диагностика всех проблем"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("COMPREHENSIVE DIAGNOSIS:")
    print("=" * 60)
    print(f"Date: {today}")
    
    # 1. Проверяем привязку ботов к городам
    print("\n1. БОТЫ ПРИВЯЗКА К ГОРОДАМ:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as total_bots,
               SUM(CASE WHEN photo_id IS NOT NULL AND photo_id != '' THEN 1 ELSE 0 END) as with_photos
        FROM profiles 
        WHERE is_bot = 1
        GROUP BY city_normalized
        ORDER BY total_bots DESC
        LIMIT 10
    ''')
    
    city_bots = cursor.fetchall()
    print("   Топ 10 городов по ботам:")
    for city, total, with_photos in city_bots:
        print(f"     {city}: {total} ботов, {with_photos} с фотками")
    
    # 2. Проверяем дубликаты фоток в городах
    print("\n2. ДУБЛИКАТЫ ФОТОК В ГОРОДАХ:")
    cursor.execute('''
        SELECT city_normalized, photo_id, COUNT(*) as duplicate_count
        FROM profiles 
        WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY city_normalized, photo_id
        HAVING duplicate_count > 1
        ORDER BY duplicate_count DESC, city_normalized
        LIMIT 20
    ''')
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"   Найдено {len(duplicates)} дубликатов:")
        for city, photo_id, count in duplicates:
            print(f"     {city}: {photo_id[:30]}... ({count} раз)")
    else:
        print("   Дубликатов не найдено")
    
    # 3. Проверяем daily_bot_order
    print("\n3. DAILY_BOT_ORDER ПРОВЕРКА:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as bots_in_order
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized
        ORDER BY bots_in_order DESC
        LIMIT 10
    ''', (today,))
    
    order_cities = cursor.fetchall()
    print("   Города с порядком на сегодня:")
    for city, count in order_cities:
        print(f"     {city}: {count} ботов в порядке")
    
    # 4. Сравниваем активных ботов и порядок
    print("\n4. СРАВНЕНИЕ АКТИВНЫХ БОТОВ И ПОРЯДКА:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as active_bots
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY city_normalized
        ORDER BY active_bots DESC
        LIMIT 10
    ''', (today,))
    
    active_cities = cursor.fetchall()
    print("   Активные боты сегодня:")
    for city, count in active_cities:
        print(f"     {city}: {count} активных ботов")
    
    # 5. Проверяем проблемы с Киевом детально
    print("\n5. КИЕВ ДЕТАЛЬНАЯ ПРОВЕРКА:")
    
    # Все боты в Киеве
    cursor.execute('''
        SELECT user_id, name, gender, photo_id, last_rotation_date
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv'
        ORDER BY gender, user_id
    ''')
    
    kyiv_all = cursor.fetchall()
    print(f"   Всего ботов в Киеве: {len(kyiv_all)}")
    
    male_count = len([b for b in kyiv_all if b[2] == 'male'])
    female_count = len([b for b in kyiv_all if b[2] == 'female'])
    print(f"   Мужчин: {male_count}, Женщин: {female_count}")
    
    # Активные боты в Киеве
    cursor.execute('''
        SELECT user_id, name, gender, photo_id
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND last_rotation_date = ?
        ORDER BY gender, user_id
    ''', (today,))
    
    kyiv_active = cursor.fetchall()
    print(f"   Активных сегодня: {len(kyiv_active)}")
    
    # Боты в порядке для Киева
    cursor.execute('''
        SELECT p.user_id, p.name, p.gender, p.photo_id, dbo.order_index
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = 'Kyiv' AND dbo.date = ?
        ORDER BY dbo.order_index
    ''', (today,))
    
    kyiv_order = cursor.fetchall()
    print(f"   В порядке: {len(kyiv_order)}")
    
    # 6. Проверяем дубликаты фоток в Киеве
    print("\n6. ДУБЛИКАТЫ ФОТОК В КИЕВЕ:")
    cursor.execute('''
        SELECT photo_id, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND photo_id IS NOT NULL AND photo_id != ''
        GROUP BY photo_id
        HAVING count > 1
        ORDER BY count DESC
    ''')
    
    kyiv_duplicates = cursor.fetchall()
    if kyiv_duplicates:
        print(f"   Дубликаты в Киеве: {len(kyiv_duplicates)}")
        for photo_id, count in kyiv_duplicates:
            print(f"     {photo_id[:30]}... ({count} раз)")
            
            # Показываем ботов с этим фото
            cursor.execute('''
                SELECT user_id, name, gender
                FROM profiles 
                WHERE is_bot = 1 AND city_normalized = 'Kyiv' AND photo_id = ?
            ''', (photo_id,))
            
            bots_with_photo = cursor.fetchall()
            print(f"       Боты с этим фото:")
            for bot_id, name, gender in bots_with_photo:
                print(f"         {name} ({gender})")
    else:
        print("   Дубликатов в Киеве не найдено")
    
    # 7. Проверяем уникальность фоток в порядке
    print("\n7. УНИКАЛЬНОСТЬ ФОТОК В ПОРЯДКЕ КИЕВА:")
    cursor.execute('''
        SELECT p.photo_id, COUNT(*) as count
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = 'Kyiv' AND dbo.date = ? AND p.photo_id IS NOT NULL AND p.photo_id != ''
        GROUP BY p.photo_id
        HAVING count > 1
        ORDER BY count DESC
    ''', (today,))
    
    order_duplicates = cursor.fetchall()
    if order_duplicates:
        print(f"   Дубликаты в порядке Киева: {len(order_duplicates)}")
        for photo_id, count in order_duplicates:
            print(f"     {photo_id[:30]}... ({count} раз)")
    else:
        print("   Дубликатов в порядке Киева не найдено")
    
    # 8. Проверяем другие города на дубликаты
    print("\n8. ДУБЛИКАТЫ В ДРУГИХ ГОРОДАХ:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as duplicate_count
        FROM (
            SELECT city_normalized, photo_id
            FROM profiles 
            WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ''
            GROUP BY city_normalized, photo_id
            HAVING COUNT(*) > 1
        ) duplicates
        GROUP BY city_normalized
        ORDER BY duplicate_count DESC
        LIMIT 10
    ''')
    
    cities_with_duplicates = cursor.fetchall()
    if cities_with_duplicates:
        print(f"   Города с дубликатами:")
        for city, count in cities_with_duplicates:
            print(f"     {city}: {count} дубликатов")
    else:
        print("   Городов с дубликатами не найдено")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE!")
    print("\nPROBLEMS FOUND:")
    print("1. Check city binding")
    print("2. Check photo duplicates")
    print("3. Check daily order consistency")
    print("4. Check gender balance")

if __name__ == "__main__":
    comprehensive_diagnosis()
