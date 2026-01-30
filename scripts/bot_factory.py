#!/usr/bin/env python3
"""
Bot Factory - Генератор ботов-аккаунтов для системы знакомств
Создает реалистичные анкеты с фото для визуальной активности
"""

import os
import sys
import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Database
from helpers.city_normalizer import normalize_city_name

class BotFactory:
    def __init__(self):
        self.db = Database()
        
        # Список городов для ботов
        self.bot_cities = [
            "Москва", "Санкт-Петербург", "Киев", "Минск", "Новосибирск",
            "Екатеринбург", "Ташкент", "Казань", "Харьков", "Нижний Новгород",
            "Челябинск", "Алматы", "Самара", "Уфа", "Ростов-на-Дону",
            "Красноярск", "Омск", "Воронеж", "Пермь", "Волгоград",
            "Одесса", "Краснодар", "Днепр", "Саратов", "Донецк",
            "Тюмень", "Тольятти", "Львов", "Запорожье", "Ижевск",
            "Барнаул", "Кривой Рог", "Ульяновск", "Иркутск", "Хабаровск",
            "Махачкала", "Владивосток", "Ярославль", "Оренбург", "Томск",
            "Кемерово", "Рязань", "Набережные Челны", "Астана", "Пенза",
            "Киров", "Липецк", "Чебоксары", "Балашиха", "Николаев"
        ]
        
        # Славянские имена
        self.male_names = [
            "Александр", "Максим", "Артем", "Дмитрий", "Иван", "Даниил", "Михаил",
            "Егор", "Андрей", "Никита", "Илья", "Матвей", "Тимофей", "Роман",
            "Кирилл", "Владимир", "Ярослав", "Павел", "Григорий", "Станислав",
            "Виктор", "Сергей", "Олег", "Юрий", "Валентин", "Виталий", "Ростислав",
            "Захар", "Макар", "Федор", "Константин", "Богдан", "Тарас", "Руслан",
            "Алексей", "Станислав", "Вадим", "Роберт", "Эдуард", "Георгий", "Лев",
            "Марк", "Денис", "Платон", "Арсений", "Всеволод", "Тимур", "Глеб"
        ]
        
        self.female_names = [
            "Анастасия", "Мария", "Дарья", "Анна", "Елизавета", "София", "Полина",
            "Виктория", "Александра", "Ева", "Ксения", "Валерия", "Милана", "Вероника",
            "Алиса", "Диана", "Карина", "Екатерина", "Ольга", "Наталья", "Татьяна",
            "Светлана", "Ирина", "Людмила", "Галина", "Елена", "Оксана", "Надежда",
            "Любовь", "Инна", "Лариса", "Марина", "Юлия", "Кристина", "Яна",
            "Олеся", "Ангелина", "Маргарита", "Дарина", "Снежана", "Алина", "Элина",
            "Майя", "Лилия", "Роза", "Влада", "Света", "Таисия", "Василиса"
        ]
        
        # Любимые напитки
        self.drinks = [
            "Коктейль", "Вино", "Пиво", "Шампанское", "Виски", "Джин-тоник",
            "Мохито", "Кровавая Мэри", "Маргарита", "Пина Колада", "Лонг Айленд",
            "Мартини", "Текила", "Ром кола", "Кофе", "Чай", "Сок", "Лимонад",
            "Водка", "Коньяк", "Бренди", "Кальвадос", "Саке", "Сидр", "Глинтвейн"
        ]
        
        # Предпочтения по оплате с учетом гендера
        self.male_payment_prefs = [
            ("i_treat", 0.7),      # 70% - я угощаю
            ("each_self", 0.25),   # 25% - каждый платит за себя  
            ("someone_treats", 0.05) # 5% - кто-то угощает (очень редко)
        ]
        
        self.female_payment_prefs = [
            ("someone_treats", 0.6), # 60% - кто-то угощает
            ("each_self", 0.3),      # 30% - каждый платит за себя
            ("i_treat", 0.1)         # 10% - я угощаю (редко)
        ]

    def get_photo_files(self, gender: str) -> List[str]:
        """Получить список файлов фото для указанного гендера"""
        folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  "assets", "bots", gender)
        
        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            return []
        
        files = []
        for ext in ['jpg', 'jpeg', 'png', 'gif']:
            files.extend([f for f in os.listdir(folder_path) 
                         if f.lower().endswith(ext)])
        
        print(f"Found {len(files)} photos in folder {folder_path}")
        return files

    def generate_bot_profile(self, gender: str, photo_path: str) -> Dict[str, Any]:
        """Сгенерировать профиль бота"""
        # Выбор имени в зависимости от гендера
        if gender == "male":
            name = random.choice(self.male_names)
            payment_prefs = self.male_payment_prefs
        else:
            name = random.choice(self.female_names)
            payment_prefs = self.female_payment_prefs
        
        # Выбор возраста (18-25 лет)
        age = random.randint(18, 25)
        
        # Выбор города
        city = random.choice(self.bot_cities)
        
        # Нормализация города - используем английские названия для базы
        city_mapping = {
            "Москва": "Moscow",
            "Санкт-Петербург": "Saint Petersburg", 
            "Киев": "Kyiv",
            "Минск": "Minsk",
            "Новосибирск": "Novosibirsk",
            "Екатеринбург": "Yekaterinburg",
            "Ташкент": "Tashkent",
            "Казань": "Kazan",
            "Харьков": "Kharkiv",
            "Нижний Новгород": "Nizhny Novgorod",
            "Челябинск": "Chelyabinsk",
            "Алматы": "Almaty",
            "Самара": "Samara",
            "Уфа": "Ufa",
            "Ростов-на-Дону": "Rostov-on-Don",
            "Красноярск": "Krasnoyarsk",
            "Омск": "Omsk",
            "Воронеж": "Voronezh",
            "Пермь": "Perm",
            "Волгоград": "Volgograd",
            "Одесса": "Odesa",
            "Краснодар": "Krasnodar",
            "Днепр": "Dnipro",
            "Саратов": "Saratov",
            "Донецк": "Donetsk",
            "Тюмень": "Tyumen",
            "Тольятти": "Tolyatti",
            "Львов": "Lviv",
            "Запорожье": "Zaporizhzhia",
            "Ижевск": "Izhevsk",
            "Барнаул": "Barnaul",
            "Кривой Рог": "Kryvyi Rih",
            "Ульяновск": "Ulyanovsk",
            "Иркутск": "Irkutsk",
            "Хабаровск": "Khabarovsk",
            "Махачкала": "Makhachkala",
            "Владивосток": "Vladivostok",
            "Ярославль": "Yaroslavl",
            "Оренбург": "Orenburg",
            "Томск": "Tomsk",
            "Кемерово": "Kemerovo",
            "Рязань": "Ryazan",
            "Набережные Челны": "Naberezhnye Chelny",
            "Астана": "Astana",
            "Пенза": "Penza",
            "Киров": "Kirov",
            "Липецк": "Lipetsk",
            "Чебоксары": "Cheboksary",
            "Балашиха": "Balashikha",
            "Николаев": "Mykolaiv"
        }
        
        city_normalized = city_mapping.get(city, city.replace(" ", "_"))
        
        # Выбор напитка
        drink = random.choice(self.drinks)
        
        # Выбор предпочтений по оплате с учетом вероятностей
        payment_choices = [pref[0] for pref in payment_prefs]
        payment_weights = [pref[1] for pref in payment_prefs]
        who_pays = random.choices(payment_choices, weights=payment_weights)[0]
        
        # Генерация user_id (отрицательные чтобы не пересекаться с реальными)
        user_id = -random.randint(1000000, 9999999)
        
        # Генерация username
        username = f"bot_{name.lower()}_{abs(user_id)}"
        
        return {
            'user_id': user_id,
            'username': username,
            'name': name,
            'age': age,
            'gender': gender,
            'city': city,
            'city_display': city,
            'city_normalized': city_normalized,
            'favorite_drink': drink,
            'photo_id': f'AgACAgIAAxkDAAIBOGf6T7X8Y7x9v2w3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9',  # Placeholder photo_id
            'who_pays': who_pays,
            'language': random.choice(['ru', 'ua']),
            'is_bot': 1,
            'bot_photo_path': photo_path.replace('\\', '/'),  # Исправляем разделители
            'last_rotation_date': None
        }

    def create_bot_in_db(self, profile: Dict[str, Any]) -> bool:
        """Создать бота в базе данных"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO profiles (
                        user_id, username, name, age, gender, city, city_display,
                        city_normalized, favorite_drink, photo_id, who_pays, language,
                        is_bot, bot_photo_path, last_rotation_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile['user_id'], profile['username'], profile['name'],
                    profile['age'], profile['gender'], profile['city'],
                    profile['city_display'], profile['city_normalized'],
                    profile['favorite_drink'], profile['photo_id'], profile['who_pays'],
                    profile['language'], profile['is_bot'], profile['bot_photo_path'],
                    profile['last_rotation_date']
                ))
                
                conn.commit()
                print(f"Created bot: {profile['name']}, {profile['age']}, {profile['city']}")
                return True
                
        except Exception as e:
            print(f"Error creating bot: {e}")
            return False

    def generate_all_bots(self):
        """Сгенерировать всех ботов из папок с фото"""
        print("Starting bot generation...")
        
        # Генерация мужских ботов
        male_photos = self.get_photo_files("male")
        for photo_file in male_photos:
            photo_path = os.path.join("assets", "bots", "male", photo_file)
            profile = self.generate_bot_profile("male", photo_path)
            self.create_bot_in_db(profile)
        
        # Генерация женских ботов
        female_photos = self.get_photo_files("female")
        for photo_file in female_photos:
            photo_path = os.path.join("assets", "bots", "female", photo_file)
            profile = self.generate_bot_profile("female", photo_path)
            self.create_bot_in_db(profile)
        
        print(f"Generation completed! Created bots: {len(male_photos)} male, {len(female_photos)} female")

if __name__ == "__main__":
    factory = BotFactory()
    factory.generate_all_bots()
