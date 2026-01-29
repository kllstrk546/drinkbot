import sqlite3
from datetime import datetime
import random

def daily_rotation():
    """Ежедневная ротация ботов - меняет порядок и активных ботов"""
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("DAILY BOT ROTATION:")
    print("=" * 50)
    print(f"Date: {today}")
    
    # 1. Получаем конфигурацию городов
    city_tiers = {
        # Tier 1 - Крупнейшие города (15 ботов на гендер)
        "Москва": 15, "Санкт-Петербург": 15, "Киев": 15, "Минск": 15,
        
        # Tier 2 - Большие города (10 ботов на гендер)
        "Новосибирск": 10, "Екатеринбург": 10, "Ташкент": 10, "Казань": 10,
        "Харьков": 10, "Нижний Новгород": 10, "Челябинск": 10, "Алматы": 10,
        "Самара": 10, "Уфа": 10, "Ростов-на-Дону": 10, "Красноярск": 10,
        "Омск": 10, "Воронеж": 10, "Пермь": 10, "Волгоград": 10,
        
        # Tier 3 - Средние города (7 ботов на гендер)
        "Одесса": 7, "Краснодар": 7, "Днепр": 7, "Саратов": 7, "Донецк": 7,
        "Тюмень": 7, "Тольятти": 7, "Львов": 7, "Запорожье": 7, "Ижевск": 7,
        "Барнаул": 7, "Кривой Рог": 7, "Ульяновск": 7, "Иркутск": 7, "Хабаровск": 7,
        
        # Tier 4 - Маленькие города (5 ботов на гендер)
        "Махачкала": 5, "Владивосток": 5, "Ярославль": 5, "Оренбург": 5, "Томск": 5,
        "Кемерово": 5, "Рязань": 5, "Набережные Челны": 5, "Астана": 5, "Пенза": 5,
        "Киров": 5, "Липецк": 5, "Чебоксары": 5, "Балашиха": 5, "Николаев": 5
    }
    
    # 2. Для каждого города делаем ротацию
    for city, bots_per_gender in city_tiers.items():
        print(f"\nProcessing {city} ({bots_per_gender} per gender)...")
        
        # Нормализуем город
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
        
        city_normalized = city_mappings.get(city.lower(), city)
        
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
        
        print(f"  Available: {len(male_bots)} male, {len(female_bots)} female")
        
        if len(male_bots) == 0 or len(female_bots) == 0:
            print(f"  Skipping {city} - no bots available")
            continue
        
        # Перемешиваем боты
        random.shuffle(male_bots)
        random.shuffle(female_bots)
        
        # Выбираем активных ботов
        active_male = male_bots[:bots_per_gender]
        active_female = female_bots[:bots_per_gender]
        
        # Объединяем и перемешиваем для разнообразия порядка
        all_active = active_male + active_female
        random.shuffle(all_active)
        
        # Обновляем last_rotation_date для активных ботов
        active_bot_ids = [bot[0] for bot in all_active]
        
        # Сначала сбрасываем всем боту в городе last_rotation_date
        cursor.execute('''
            UPDATE profiles 
            SET last_rotation_date = NULL 
            WHERE is_bot = 1 AND city_normalized = ?
        ''', (city_normalized,))
        
        # Устанавливаем сегодняшнюю дату для активных ботов
        if active_bot_ids:
            placeholders = ','.join(['?' for _ in active_bot_ids])
            cursor.execute(f'''
                UPDATE profiles 
                SET last_rotation_date = ? 
                WHERE user_id IN ({placeholders})
            ''', [today] + active_bot_ids)
        
        # Создаем порядок на день
        cursor.execute('DELETE FROM daily_bot_order WHERE city_normalized = ? AND date = ?', (city_normalized, today))
        
        for i, bot in enumerate(all_active):
            user_id, name, gender = bot
            cursor.execute('''
                INSERT INTO daily_bot_order (city_normalized, bot_user_id, order_index, date)
                VALUES (?, ?, ?, ?)
            ''', (city_normalized, user_id, i, today))
        
        print(f"  Activated: {len(active_male)} male, {len(active_female)} female")
    
    conn.commit()
    
    # 3. Проверяем результат
    print(f"\nROTATION SUMMARY:")
    cursor.execute('''
        SELECT city_normalized, COUNT(*) as count
        FROM profiles 
        WHERE is_bot = 1 AND last_rotation_date = ?
        GROUP BY city_normalized
        ORDER BY count DESC
        LIMIT 10
    ''', (today,))
    
    summary = cursor.fetchall()
    for city, count in summary:
        print(f"  {city}: {count} active bots")
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND last_rotation_date = ?', (today,))
    total_active = cursor.fetchone()[0]
    print(f"\nTotal active bots today: {total_active}")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("DAILY ROTATION COMPLETE!")
    print(f"All bots will have the same order throughout {today}")

if __name__ == "__main__":
    daily_rotation()
