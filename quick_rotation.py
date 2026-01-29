#!/usr/bin/env python3
"""
Быстрая ротация ботов без зависаний
"""

import sqlite3
import random
from datetime import datetime

def quick_rotation():
    """Быстрая ротация ботов"""
    
    # Распределение ботов по городам
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
    
    # Простая нормализация городов
    city_mapping = {
        "Москва": "Moscow", "Санкт-Петербург": "Saint Petersburg", "Киев": "Kyiv", "Минск": "Minsk",
        "Новосибирск": "Novosibirsk", "Екатеринбург": "Yekaterinburg", "Ташкент": "Tashkent", "Казань": "Kazan",
        "Харьков": "Kharkiv", "Нижний Новгород": "Nizhny Novgorod", "Челябинск": "Chelyabinsk", "Алматы": "Almaty",
        "Самара": "Samara", "Уфа": "Ufa", "Ростов-на-Дону": "Rostov-on-Don", "Красноярск": "Krasnoyarsk",
        "Омск": "Omsk", "Воронеж": "Voronezh", "Пермь": "Perm", "Волгоград": "Volgograd",
        "Одесса": "Odesa", "Краснодар": "Krasnodar", "Днепр": "Dnipro", "Саратов": "Saratov",
        "Донецк": "Donetsk", "Тюмень": "Tyumen", "Тольятти": "Tolyatti", "Львов": "Lviv",
        "Запорожье": "Zaporizhzhia", "Ижевск": "Izhevsk", "Барнаул": "Barnaul", "Кривой Рог": "Kryvyi Rih",
        "Ульяновск": "Ulyanovsk", "Иркутск": "Irkutsk", "Хабаровск": "Khabarovsk", "Махачкала": "Makhachkala",
        "Владивосток": "Vladivostok", "Ярославль": "Yaroslavl", "Оренбург": "Orenburg", "Томск": "Tomsk",
        "Кемерово": "Kemerovo", "Рязань": "Ryazan", "Набережные Челны": "Naberezhnye Chelny", "Астана": "Astana",
        "Пенза": "Penza", "Киров": "Kirov", "Липецк": "Lipetsk", "Чебоксары": "Cheboksary",
        "Балашиха": "Balashikha", "Николаев": "Mykolaiv"
    }
    
    conn = sqlite3.connect('drink_bot.db')
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    total_activated = 0
    
    print(f"Starting quick rotation for {today}")
    print("=" * 50)
    
    for city, bots_per_gender in city_tiers.items():
        city_normalized = city_mapping.get(city, city.replace(" ", "_"))
        
        print(f"\n=== {city} ({city_normalized}) ===")
        print(f"Target: {bots_per_gender} bots per gender")
        
        # Получаем ботов для этого города
        cursor.execute('''
            SELECT user_id, gender FROM profiles 
            WHERE is_bot = 1 AND city_normalized = ?
            ORDER BY RANDOM()
        ''', (city_normalized,))
        
        available_bots = cursor.fetchall()
        male_bots = [bot[0] for bot in available_bots if bot[1] == 'male']
        female_bots = [bot[0] for bot in available_bots if bot[1] == 'female']
        
        print(f"Available: {len(male_bots)} male, {len(female_bots)} female")
        
        # Выбираем активных ботов
        active_male = male_bots[:bots_per_gender]
        active_female = female_bots[:bots_per_gender]
        active_bots = active_male + active_female
        
        print(f"Selected: {len(active_male)} male, {len(active_female)} female")
        
        # Обновляем дату ротации
        if active_bots:
            placeholders = ','.join(['?' for _ in active_bots])
            cursor.execute(f'''
                UPDATE profiles 
                SET last_rotation_date = ? 
                WHERE user_id IN ({placeholders}) AND is_bot = 1
            ''', [today] + active_bots)
            
            total_activated += len(active_bots)
            print(f"OK Updated {len(active_bots)} bots")
        else:
            print(f"WARNING No bots available")
    
    conn.commit()
    conn.close()
    
    print(f"\n" + "=" * 50)
    print(f"ROTATION COMPLETE!")
    print(f"Total bots activated: {total_activated}")
    print(f"Cities processed: {len(city_tiers)}")

if __name__ == "__main__":
    quick_rotation()
