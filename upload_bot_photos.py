#!/usr/bin/env python3
"""
Загрузка фото ботов в Telegram
"""

import os
import sys
import sqlite3
import asyncio
from aiogram import Bot, types
from datetime import datetime

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Читаем токен из .env файла
def get_bot_token():
    env_path = os.path.join(os.path.dirname(__file__), 'bot.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('BOT_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return None

BOT_TOKEN = get_bot_token()

class BotPhotoUploader:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.bot_folder = "assets/bots"
        
    def get_bot_photos(self):
        """Получить список всех фото ботов"""
        photos = []
        
        # Мужские фото
        male_folder = os.path.join(self.bot_folder, "male")
        if os.path.exists(male_folder):
            for filename in os.listdir(male_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    photos.append({
                        'path': os.path.join(male_folder, filename),
                        'filename': filename,
                        'gender': 'male'
                    })
        
        # Женские фото
        female_folder = os.path.join(self.bot_folder, "female")
        if os.path.exists(female_folder):
            for filename in os.listdir(female_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    photos.append({
                        'path': os.path.join(female_folder, filename),
                        'filename': filename,
                        'gender': 'female'
                    })
        
        return photos
    
    def get_bots_without_photos(self):
        """Получить ботов без фото"""
        conn = sqlite3.connect('drink_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, gender, city_normalized 
            FROM profiles 
            WHERE is_bot = 1 
            AND (photo_id IS NULL OR photo_id = '')
            ORDER BY gender, city_normalized
        ''')
        
        bots = cursor.fetchall()
        conn.close()
        
        return bots
    
    def match_photos_to_bots(self, bots, photos):
        """Сопоставить фото с ботами по гендеру"""
        male_photos = [p for p in photos if p['gender'] == 'male']
        female_photos = [p for p in photos if p['gender'] == 'female']
        
        matches = []
        
        for bot in bots:
            bot_gender = bot[2]
            
            if bot_gender == 'male' and male_photos:
                photo = male_photos.pop(0)
                matches.append({
                    'bot_id': bot[0],
                    'bot_name': bot[1],
                    'photo_path': photo['path'],
                    'gender': bot_gender
                })
            elif bot_gender == 'female' and female_photos:
                photo = female_photos.pop(0)
                matches.append({
                    'bot_id': bot[0],
                    'bot_name': bot[1],
                    'photo_path': photo['path'],
                    'gender': bot_gender
                })
        
        return matches
    
    async def upload_photo_to_telegram(self, photo_path):
        """Загрузить фото в Telegram и получить file_id"""
        try:
            # Отправляем фото реальному пользователю (тебе)
            message = await self.bot.send_photo(
                chat_id=5483644714,  # ID реального пользователя
                photo=types.FSInputFile(photo_path),
                caption=f"Uploading bot photo: {os.path.basename(photo_path)}"
            )
            
            # Получаем file_id
            file_id = message.photo[-1].file_id
            
            # Удаляем временное сообщение
            await self.bot.delete_message(
                chat_id=5483644714,
                message_id=message.message_id
            )
            
            return file_id
            
        except Exception as e:
            print(f"Error uploading photo {photo_path}: {e}")
            return None
    
    async def update_bot_photo(self, bot_id, photo_id):
        """Обновить photo_id бота в базе данных"""
        try:
            conn = sqlite3.connect('drink_bot.db')
            cursor = conn.cursor()
            
            cursor.execute('UPDATE profiles SET photo_id = ? WHERE user_id = ?', (photo_id, bot_id))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error updating bot {bot_id} photo: {e}")
            return False
    
    async def upload_all_photos(self, limit=10):
        """Загрузить все фото ботов"""
        print("Начинаю загрузку фото ботов...")
        
        # Получаем ботов без фото
        bots = self.get_bots_without_photos()
        print(f"Найдено ботов без фото: {len(bots)}")
        
        # Получаем доступные фото
        photos = self.get_bot_photos()
        print(f"Доступно фото: {len(photos)}")
        
        if not bots:
            print("Все боты уже имеют фото!")
            return
        
        if not photos:
            print("Нет доступных фото для загрузки!")
            return
        
        # Сопоставляем фото с ботами
        matches = self.match_photos_to_bots(bots, photos)
        print(f"Сопоставлено пар бот-фото: {len(matches)}")
        
        # Ограничиваем количество для теста
        matches = matches[:limit]
        print(f"Загружаем первые {len(matches)} фото...")
        
        # Загружаем фото
        uploaded_count = 0
        
        for i, match in enumerate(matches):
            print(f"\n[{i+1}/{len(matches)}] Загружаю фото для бота {match['bot_name']} (ID: {match['bot_id']})")
            print(f"   Фото: {match['photo_path']}")
            
            # Загружаем фото в Telegram
            photo_id = await self.upload_photo_to_telegram(match['photo_path'])
            
            if photo_id:
                # Обновляем бота в базе
                if await self.update_bot_photo(match['bot_id'], photo_id):
                    print(f"   OK Фото успешно загружено: {photo_id}")
                    uploaded_count += 1
                else:
                    print(f"   ERROR Ошибка обновления бота в базе")
            else:
                print(f"   ERROR Ошибка загрузки фото")
        
        print(f"\nЗагрузка завершена! Успешно загружено: {uploaded_count}/{len(matches)}")
        
        # Проверяем результат
        conn = sqlite3.connect('drink_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1 AND photo_id IS NOT NULL AND photo_id != ""')
        bots_with_photos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM profiles WHERE is_bot = 1')
        total_bots = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"Статистика: {bots_with_photos}/{total_bots} ботов имеют фото")

async def main():
    """Главная функция"""
    uploader = BotPhotoUploader()
    
    # Сначала загружаем 10 фото для теста
    await uploader.upload_all_photos(limit=100)
    
    # Если все хорошо, можно раскомментировать для загрузки всех фото
    # await uploader.upload_all_photos()

if __name__ == "__main__":
    asyncio.run(main())
