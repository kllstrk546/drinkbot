import sqlite3
from datetime import datetime
import random

def activate_all_bots():
    """Активация всех ботов с правильными данными"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("ACTIVATING ALL BOTS:")
    print("=" * 60)
    print(f"Date: {today}")
    
    # 1. Проверяем текущее состояние
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1
    ''')
    total_bots = cursor.fetchone()[0]
    print(f"\n1. TOTAL BOTS IN DATABASE: {total_bots}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?
    ''', (today,))
    active_today = cursor.fetchone()[0]
    print(f"   Active today: {active_today}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date IS NULL
    ''')
    inactive_bots = cursor.fetchone()[0]
    print(f"   Inactive (NULL date): {inactive_bots}")
    
    # 2. Распределение по городам и гендеру
    print(f"\n2. TARGET DISTRIBUTION:")
    
    # Tier 1 - Главные города
    tier1_cities = {
        "Kyiv": {"male": 20, "female": 20},
        "Moscow": {"male": 20, "female": 20},
        "Saint Petersburg": {"male": 15, "female": 15},
        "Minsk": {"male": 15, "female": 15}
    }
    
    # Tier 2 - Крупные города
    tier2_cities = {
        "Novosibirsk": {"male": 12, "female": 12},
        "Yekaterinburg": {"male": 12, "female": 12},
        "Tashkent": {"male": 12, "female": 12},
        "Kazan": {"male": 12, "female": 12},
        "Kharkiv": {"male": 12, "female": 12},
        "Nizhny Novgorod": {"male": 12, "female": 12},
        "Chelyabinsk": {"male": 12, "female": 12},
        "Almaty": {"male": 12, "female": 12},
        "Samara": {"male": 12, "female": 12},
        "Ufa": {"male": 12, "female": 12},
        "Rostov-on-Don": {"male": 12, "female": 12},
        "Krasnoyarsk": {"male": 12, "female": 12},
        "Omsk": {"male": 12, "female": 12},
        "Voronezh": {"male": 12, "female": 12},
        "Perm": {"male": 12, "female": 12},
        "Volgograd": {"male": 12, "female": 12}
    }
    
    # Tier 3 - Средние города
    tier3_cities = {
        "Odesa": {"male": 8, "female": 8},
        "Krasnodar": {"male": 8, "female": 8},
        "Dnipro": {"male": 8, "female": 8},
        "Saratov": {"male": 8, "female": 8},
        "Donetsk": {"male": 8, "female": 8},
        "Tyumen": {"male": 8, "female": 8},
        "Tolyatti": {"male": 8, "female": 8},
        "Lviv": {"male": 8, "female": 8},
        "Zaporizhzhia": {"male": 8, "female": 8},
        "Izhevsk": {"male": 8, "female": 8},
        "Barnaul": {"male": 8, "female": 8},
        "Ulyanovsk": {"male": 8, "female": 8},
        "Irkutsk": {"male": 8, "female": 8},
        "Khabarovsk": {"male": 8, "female": 8},
        "Makhachkala": {"male": 8, "female": 8},
        "Vladivostok": {"male": 8, "female": 8}
    }
    
    # Tier 4 - Маленькие города
    tier4_cities = {
        "Yaroslavl": {"male": 5, "female": 5},
        "Orenburg": {"male": 5, "female": 5},
        "Tomsk": {"male": 5, "female": 5},
        "Kemerovo": {"male": 5, "female": 5},
        "Ryazan": {"male": 5, "female": 5},
        "Naberezhnye Chelny": {"male": 5, "female": 5},
        "Astana": {"male": 5, "female": 5},
        "Penza": {"male": 5, "female": 5},
        "Kirov": {"male": 5, "female": 5},
        "Lipetsk": {"male": 5, "female": 5},
        "Cheboksary": {"male": 5, "female": 5},
        "Balashikha": {"male": 5, "female": 5},
        "Mykolaiv": {"male": 5, "female": 5}
    }
    
    all_cities = {**tier1_cities, **tier2_cities, **tier3_cities, **tier4_cities}
    
    total_target = sum(
        sum(gender_counts.values()) 
        for gender_counts in all_cities.values()
    )
    print(f"   Target total bots: {total_target}")
    
    # 3. Активируем всех ботов
    print(f"\n3. ACTIVATING ALL BOTS:")
    
    # Сначала активируем всех неактивных ботов
    cursor.execute('''
        UPDATE profiles 
        SET last_rotation_date = ?
        WHERE is_bot = 1 AND last_rotation_date IS NULL
    ''', (today,))
    
    activated_count = cursor.rowcount
    print(f"   Activated {activated_count} inactive bots")
    
    # 4. Создаем daily_bot_order для всех городов
    print(f"\n4. CREATING DAILY_BOT_ORDER:")
    
    # Удаляем старые записи
    cursor.execute('DELETE FROM daily_bot_order WHERE date = ?', (today,))
    
    # Получаем всех активных ботов
    cursor.execute('''
        SELECT user_id, city_normalized, gender
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        ORDER BY city_normalized, gender, user_id
    ''', (today,))
    
    all_active_bots = cursor.fetchall()
    print(f"   Found {len(all_active_bots)} active bots")
    
    # Распределяем по городам
    city_bots = {}
    for user_id, city, gender in all_active_bots:
        if city not in city_bots:
            city_bots[city] = {"male": [], "female": []}
        city_bots[city][gender].append(user_id)
    
    # Создаем порядок для каждого города
    total_order_entries = 0
    for city, bot_lists in city_bots.items():
        all_city_bots = []
        
        # Добавляем мужчин
        for bot_id in bot_lists.get("male", []):
            all_city_bots.append(bot_id)
        
        # Добавляем женщин
        for bot_id in bot_lists.get("female", []):
            all_city_bots.append(bot_id)
        
        # Перемешиваем для разнообразия
        random.shuffle(all_city_bots)
        
        # Создаем записи в daily_bot_order
        for order_index, bot_id in enumerate(all_city_bots):
            cursor.execute('''
                INSERT INTO daily_bot_order (bot_user_id, city_normalized, date, order_index)
                VALUES (?, ?, ?, ?)
            ''', (bot_id, city, today, order_index))
            total_order_entries += 1
    
    print(f"   Created {total_order_entries} daily order entries")
    
    # 5. Проверяем результат
    print(f"\n5. VERIFICATION:")
    
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM daily_bot_order 
        WHERE date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 10
    ''', (today,))
    
    top_cities = cursor.fetchall()
    print(f"   Top 10 cities by bot count:")
    for city, count in top_cities:
        print(f"     {city}: {count} bots")
    
    # 6. Проверяем наличие фотографий
    print(f"\n6. PHOTO VERIFICATION:")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ? AND photo_id IS NOT NULL
    ''', (today,))
    
    bots_with_photos = cursor.fetchone()[0]
    print(f"   Bots with photos: {bots_with_photos}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ? AND photo_id IS NULL
    ''', (today,))
    
    bots_without_photos = cursor.fetchone()[0]
    print(f"   Bots without photos: {bots_without_photos}")
    
    if bots_without_photos > 0:
        print(f"   WARNING: {bots_without_photos} bots have no photos!")
    
    # 7. Проверяем гендерное распределение
    print(f"\n7. GENDER DISTRIBUTION:")
    
    cursor.execute('''
        SELECT gender, COUNT(*) FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY gender
    ''', (today,))
    
    gender_dist = cursor.fetchall()
    for gender, count in gender_dist:
        print(f"   {gender}: {count} bots")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 60)
    print("ALL BOTS ACTIVATION COMPLETE!")
    print(f"\nSUMMARY:")
    print(f"✅ Total bots: {total_bots}")
    print(f"✅ Activated today: {activated_count + active_today}")
    print(f"✅ Daily order entries: {total_order_entries}")
    print(f"✅ Cities with bots: {len(city_bots)}")
    print(f"✅ Bots with photos: {bots_with_photos}")
    
    if bots_without_photos > 0:
        print(f"⚠️  Bots without photos: {bots_without_photos}")
    
    print(f"\n🚀 ALL BOTS READY FOR DATING!")

if __name__ == "__main__":
    activate_all_bots()
