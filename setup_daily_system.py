import sqlite3
from datetime import datetime
import random

def setup_daily_system():
    """Настраиваем полную ежедневную систему"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("SETTING UP DAILY SYSTEM:")
    print("=" * 50)
    print(f"Date: {today}")
    
    # 1. Создаем таблицу для ежедневного порядка
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_bot_order (
            city_normalized TEXT,
            bot_user_id INTEGER,
            order_index INTEGER,
            date TEXT,
            PRIMARY KEY (city_normalized, bot_user_id, date)
        )
    ''')
    
    # 2. Получаем конфигурацию городов
    city_tiers = {
        "Киев": 15, "Москва": 15, "Санкт-Петербург": 15, "Минск": 15,
        "Новосибирск": 10, "Екатеринбург": 10, "Ташкент": 10, "Казань": 10,
        "Харьков": 10, "Нижний Новгород": 10, "Челябинск": 10, "Алматы": 10,
        "Самара": 10, "Уфа": 10, "Ростов-на-Дону": 10, "Красноярск": 10,
        "Омск": 10, "Воронеж": 10, "Пермь": 10, "Волгоград": 10,
        "Одесса": 7, "Краснодар": 7, "Днепр": 7, "Саратов": 7, "Донецк": 7,
        "Тюмень": 7, "Тольятти": 7, "Львов": 7, "Запорожье": 7, "Ижевск": 7,
        "Барнаул": 7, "Кривой Рог": 7, "Ульяновск": 7, "Иркутск": 7, "Хабаровск": 7,
        "Махачкала": 5, "Владивосток": 5, "Ярославль": 5, "Оренбург": 5, "Томск": 5,
        "Кемерово": 5, "Рязань": 5, "Набережные Челны": 5, "Астана": 5, "Пенза": 5,
        "Киров": 5, "Липецк": 5, "Чебоксары": 5, "Балашиха": 5, "Николаев": 5
    }
    
    # 3. Маппинг городов
    city_mappings = {
        "москва": "Moscow", "киев": "Kyiv", "санкт-петербург": "Saint Petersburg",
        "минск": "Minsk", "харьков": "Kharkiv", "одесса": "Odesa", "днепр": "Dnipro",
        "донецк": "Donetsk", "запорожье": "Zaporizhzhia", "львов": "Lviv",
        "новосибирск": "Novosibirsk", "екатеринбург": "Yekaterinburg", "ташкент": "Tashkent",
        "казань": "Kazan", "нижний новгород": "Nizhny Novgorod", "челябинск": "Chelyabinsk",
        "алматы": "Almaty", "самара": "Samara", "уфа": "Ufa", "ростов-на-дону": "Rostov-on-Don",
        "красноярск": "Krasnoyarsk", "омск": "Omsk", "воронеж": "Voronezh", "пермь": "Perm",
        "волгоград": "Volgograd", "краснодар": "Krasnodar", "саратов": "Saratov", "тюмень": "Tyumen",
        "тольятти": "Tolyatti", "барнаул": "Barnaul", "ульяновск": "Ulyanovsk", "иркутск": "Irkutsk",
        "хабаровск": "Khabarovsk", "махачкала": "Makhachkala", "владивосток": "Vladivostok",
        "ярославль": "Yaroslavl", "оренбург": "Orenburg", "томск": "Tomsk", "кемерово": "Kemerovo",
        "рязань": "Ryazan", "набережные челны": "Naberezhnye Chelny", "астана": "Astana",
        "пенза": "Penza", "киров": "Kirov", "липецк": "Lipetsk", "чебоксары": "Cheboksary",
        "балашиха": "Balashikha", "николаев": "Mykolaiv"
    }
    
    # 4. Для каждого города создаем порядок
    for city, bots_per_gender in city_tiers.items():
        city_normalized = city_mappings.get(city.lower(), city)
        
        print(f"\nProcessing {city} ({city_normalized})...")
        
        # Получаем всех ботов для города
        cursor.execute('''
            SELECT user_id, name, gender
            FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ?
            ORDER BY gender, user_id
        ''', (city_normalized,))
        
        all_bots = cursor.fetchall()
        male_bots = [b for b in all_bots if b[2] == 'male']
        female_bots = [b for b in all_bots if b[2] == 'female']
        
        if len(male_bots) == 0 or len(female_bots) == 0:
            print(f"  Skipping {city} - no bots available")
            continue
        
        # Перемешиваем и выбираем активных
        random.shuffle(male_bots)
        random.shuffle(female_bots)
        
        active_male = male_bots[:bots_per_gender]
        active_female = female_bots[:bots_per_gender]
        
        # Объединяем и перемешиваем
        all_active = active_male + active_female
        random.shuffle(all_active)
        
        # Обновляем last_rotation_date
        active_bot_ids = [bot[0] for bot in all_active]
        
        cursor.execute('''
            UPDATE profiles 
            SET last_rotation_date = NULL 
            WHERE is_bot = 1 AND city_normalized = ?
        ''', (city_normalized,))
        
        if active_bot_ids:
            placeholders = ','.join(['?' for _ in active_bot_ids])
            cursor.execute(f'''
                UPDATE profiles 
                SET last_rotation_date = ? 
                WHERE user_id IN ({placeholders})
            ''', [today] + active_bot_ids)
        
        # Создаем порядок для доступных ботов
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city_normalized, today))
        
        for i, bot in enumerate(all_active):
            bot_user_id, name, gender = bot
            cursor.execute('''
                INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city_normalized, bot_user_id, i, today))
        
        print(f"  Activated: {len(active_male)} male, {len(active_female)} female")
    
    conn.commit()
    
    # 5. Создаем индекс
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_daily_bot_order_lookup 
        ON daily_bot_order (city_normalized, date, order_index)
    ''')
    
    conn.commit()
    
    # 6. Проверяем результат
    print(f"\nSYSTEM SETUP COMPLETE:")
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?', (today,))
    total_active = cursor.fetchone()[0]
    print(f"Total active bots today: {total_active}")
    
    cursor.execute('SELECT COUNT(DISTINCT city_normalized) FROM daily_bot_order WHERE date = ?', (today,))
    cities_with_order = cursor.fetchone()[0]
    print(f"Cities with daily order: {cities_with_order}")
    
    # 7. Тестируем для Киева
    print(f"\nKYIV TEST:")
    cursor.execute('''
        SELECT p.name, p.gender
        FROM profiles p
        JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
        WHERE p.city_normalized = 'Kyiv' AND dbo.date = ?
        ORDER BY dbo.order_index
        LIMIT 5
    ''', (today,))
    
    kyiv_bots = cursor.fetchall()
    print(f"First 5 Kyiv bots:")
    for i, bot in enumerate(kyiv_bots):
        name, gender = bot
        print(f"  {i}. {name} ({gender})")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("DAILY SYSTEM SETUP COMPLETE!")
    print("\nFEATURES:")
    print("1. Fixed order for each city")
    print("2. Same bots throughout the day")
    print("3. Daily rotation at midnight")
    print("4. Consistent gender balance")
    print("\nTO USE:")
    print("1. Run this script once per day (or schedule with cron)")
    print("2. All users will see same bots in same order")
    print("3. Order persists until next rotation")

if __name__ == "__main__":
    setup_daily_system()
