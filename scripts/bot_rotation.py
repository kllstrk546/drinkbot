#!/usr/bin/env python3
"""
Bot Rotation System - Алгоритм "Управляемого Хаоса"
Ежедневная ротация ботов для создания визуальной активности
"""

import os
import sys
import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database
from helpers.city_normalizer import normalize_city_name

class BotRotationManager:
    def __init__(self):
        self.db = Database()
        
        # Распределение ботов по важности городов
        self.city_tiers = {
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
        
        self.rotation_cities = list(self.city_tiers.keys())

    def get_all_bots(self) -> List[Dict[str, Any]]:
        """Получить всех ботов из базы данных"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, name, age, gender, city, city_normalized,
                           favorite_drink, who_pays, bot_photo_path, last_rotation_date
                    FROM profiles 
                    WHERE is_bot = 1
                ''')
                
                # Получаем данные и создаем словари вручную
                rows = cursor.fetchall()
                columns = ['user_id', 'name', 'age', 'gender', 'city', 'city_normalized',
                          'favorite_drink', 'who_pays', 'bot_photo_path', 'last_rotation_date']
                
                bots = []
                for row in rows:
                    bot_dict = {}
                    for i, column in enumerate(columns):
                        bot_dict[column] = row[i]
                    bots.append(bot_dict)
                
                print(f"Found {len(bots)} bots in database")
                return bots
                
        except Exception as e:
            print(f"Error getting bots: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_bots_by_city_and_gender(self, city_normalized: str, gender: str) -> List[Dict[str, Any]]:
        """Получить ботов для конкретного города и гендера"""
        bots = self.get_all_bots()
        return [bot for bot in bots 
                if bot['city_normalized'] == city_normalized and bot['gender'] == gender]

    def shuffle_bots(self, bots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Перемешать ботов в случайном порядке"""
        shuffled = bots.copy()
        random.shuffle(shuffled)
        return shuffled

    def update_rotation_date(self, user_ids: List[int], date: str):
        """Обновить дату ротации для указанных ботов"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Сначала сбрасываем дату ротации для всех ботов
                cursor.execute("UPDATE profiles SET last_rotation_date = NULL WHERE is_bot = 1")
                
                # Устанавливаем новую дату для активных ботов
                if user_ids:
                    placeholders = ','.join(['?' for _ in user_ids])
                    cursor.execute(f'''
                        UPDATE profiles 
                        SET last_rotation_date = ? 
                        WHERE user_id IN ({placeholders}) AND is_bot = 1
                    ''', [date] + user_ids)
                
                conn.commit()
                print(f"Updated rotation date for {len(user_ids)} bots to {date}")
                
        except Exception as e:
            print(f"Error updating rotation dates: {e}")

    def get_active_bots_for_city(self, city_normalized: str, date: str) -> List[Dict[str, Any]]:
        """Получить активных ботов для города на указанную дату"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, name, age, gender, city, city_normalized,
                           favorite_drink, who_pays, bot_photo_path, last_rotation_date
                    FROM profiles 
                    WHERE is_bot = 1 
                    AND city_normalized = ?
                    AND last_rotation_date = ?
                    ORDER BY RANDOM()
                ''', (city_normalized, date))
                
                # Получаем данные и создаем словари вручную
                rows = cursor.fetchall()
                columns = ['user_id', 'name', 'age', 'gender', 'city', 'city_normalized',
                          'favorite_drink', 'who_pays', 'bot_photo_path', 'last_rotation_date']
                
                bots = []
                for row in rows:
                    bot_dict = {}
                    for i, column in enumerate(columns):
                        bot_dict[column] = row[i]
                    bots.append(bot_dict)
                
                return bots
                
        except Exception as e:
            print(f"Error getting active bots for {city_normalized}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def rotate_bots_for_city(self, city_normalized: str, date: str):
        """Выполнить ротацию ботов для конкретного города"""
        print(f"\n=== Rotating bots for {city_normalized} ===")
        
        # Получаем количество ботов для этого города
        # Находим оригинальное название города по нормализованному
        original_city = None
        for city, bots_per_gender in self.city_tiers.items():
            if normalize_city_name(city) == city_normalized:
                original_city = city
                break
        
        if original_city:
            bots_per_gender = self.city_tiers[original_city]
        else:
            bots_per_gender = 5  # По умолчанию
        
        print(f"Target: {bots_per_gender} bots per gender for {original_city or city_normalized}")
        
        # Получаем всех ботов для города
        male_bots = self.get_bots_by_city_and_gender(city_normalized, 'male')
        female_bots = self.get_bots_by_city_and_gender(city_normalized, 'female')
        
        print(f"Available bots: {len(male_bots)} male, {len(female_bots)} female")
        
        # Перемешиваем ботов
        male_bots = self.shuffle_bots(male_bots)
        female_bots = self.shuffle_bots(female_bots)
        
        # Выбираем активных ботов (с учетом лимита города)
        active_male = male_bots[:bots_per_gender]
        active_female = female_bots[:bots_per_gender]
        
        # Собираем ID активных ботов
        active_bot_ids = [bot['user_id'] for bot in active_male + active_female]
        
        print(f"Selected {len(active_male)} male and {len(active_female)} female bots")
        
        # Обновляем дату ротации
        self.update_rotation_date(active_bot_ids, date)
        
        return active_male + active_female

    def rotate_all_cities(self, date: str = None):
        """Выполнить ротацию для всех городов"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Starting bot rotation for {date}")
        print("=" * 60)
        
        total_activated = 0
        city_stats = {}
        
        for city in self.rotation_cities:
            # Нормализуем город
            city_normalized = normalize_city_name(city)
            
            # Выполняем ротацию
            active_bots = self.rotate_bots_for_city(city_normalized, date)
            
            total_activated += len(active_bots)
            city_stats[city] = len(active_bots)
            
            # Показываем статистику по городу
            male_count = len([b for b in active_bots if b['gender'] == 'male'])
            female_count = len([b for b in active_bots if b['gender'] == 'female'])
            
            if active_bots:
                print(f"OK {city}: {male_count}M + {female_count}F = {len(active_bots)} active")
            else:
                print(f"WARNING {city}: No bots available")
        
        # Итоговая статистика
        print("\n" + "=" * 60)
        print(f"ROTATION COMPLETE!")
        print(f"Total bots activated: {total_activated}")
        print(f"Cities with bots: {len([c for c in city_stats.values() if c > 0])}/{len(self.rotation_cities)}")
        
        # Детальная статистика по городам с ботами
        active_cities = {city: count for city, count in city_stats.items() if count > 0}
        if active_cities:
            print(f"\nActive cities:")
            for city, count in sorted(active_cities.items(), key=lambda x: x[1], reverse=True):
                print(f"   * {city}: {count} bots")
        
        return city_stats

    def get_rotation_report(self, date: str = None) -> Dict[str, Any]:
        """Получить отчет о ротации на указанную дату"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\nROTATION REPORT for {date}")
        print("=" * 50)
        
        report = {
            'date': date,
            'total_active': 0,
            'cities': {},
            'gender_stats': {'male': 0, 'female': 0}
        }
        
        for city in self.rotation_cities:
            from helpers.city_normalizer import normalize_city_name
            city_normalized = normalize_city_name(city)
            
            active_bots = self.get_active_bots_for_city(city_normalized, date)
            
            if active_bots:
                male_count = len([b for b in active_bots if b['gender'] == 'male'])
                female_count = len([b for b in active_bots if b['gender'] == 'female'])
                
                report['cities'][city] = {
                    'total': len(active_bots),
                    'male': male_count,
                    'female': female_count
                }
                
                report['total_active'] += len(active_bots)
                report['gender_stats']['male'] += male_count
                report['gender_stats']['female'] += female_count
                
                print(f"LOCATION {city}: {male_count}M + {female_count}F = {len(active_bots)}")
        
        print(f"\nSUMMARY:")
        print(f"   Total active bots: {report['total_active']}")
        print(f"   Male bots: {report['gender_stats']['male']}")
        print(f"   Female bots: {report['gender_stats']['female']}")
        print(f"   Active cities: {len(report['cities'])}")
        
        return report

    def test_rotation(self):
        """Тестовая ротация для проверки системы"""
        print("TESTING ROTATION SYSTEM")
        print("=" * 40)
        
        # Используем тестовую дату
        test_date = "2024-01-29"
        
        # Выполняем ротацию
        stats = self.rotate_all_cities(test_date)
        
        # Показываем отчет
        report = self.get_rotation_report(test_date)
        
        return report

if __name__ == "__main__":
    manager = BotRotationManager()
    
    # Тестовая ротация
    manager.test_rotation()
