#!/usr/bin/env python3
"""
Bot Photo Uploader - Загрузка фото ботов в Telegram
"""

import os
import sys
import sqlite3
import asyncio
from typing import Dict, Any, List

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiogram
from aiogram import Bot
from database.models import Database

class BotPhotoUploader:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.db = Database()

    async def upload_bot_photos(self) -> Dict[str, Any]:
        """Загрузить все фото ботов в Telegram"""
        print("Starting bot photo upload...")
        
        # Получаем всех ботов без photo_id
        bots_without_photos = self.get_bots_without_photos()
        print(f"Found {len(bots_without_photos)} bots without Telegram photos")
        
        upload_stats = {
            'total': len(bots_without_photos),
            'uploaded': 0,
            'failed': 0,
            'errors': []
        }
        
        for bot in bots_without_photos:
            try:
                # Проверяем существует ли файл
                if not os.path.exists(bot['bot_photo_path']):
                    print(f"Photo file not found: {bot['bot_photo_path']}")
                    upload_stats['failed'] += 1
                    upload_stats['errors'].append(f"File not found: {bot['bot_photo_path']}")
                    continue
                
                # Загружаем фото в Telegram
                with open(bot['bot_photo_path'], 'rb') as photo_file:
                    message = await self.bot.send_photo(
                        chat_id=8503492041,  # Твой чат для загрузки
                        photo=photo_file,
                        caption=f"Bot photo upload: {bot['name']}"
                    )
                
                # Получаем file_id фото
                photo_id = message.photo[-1].file_id
                
                # Обновляем в базе
                self.update_bot_photo_id(bot['user_id'], photo_id)
                
                upload_stats['uploaded'] += 1
                print(f"Uploaded photo for bot {bot['name']} (ID: {bot['user_id']})")
                
                # Удаляем временное сообщение
                await self.bot.delete_message(chat_id=8503492041, message_id=message.message_id)
                
            except Exception as e:
                print(f"Error uploading photo for bot {bot['name']}: {e}")
                upload_stats['failed'] += 1
                upload_stats['errors'].append(f"Bot {bot['name']}: {str(e)}")
        
        return upload_stats

    def get_bots_without_photos(self) -> List[Dict[str, Any]]:
        """Получить ботов без загруженных фото"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, name, bot_photo_path 
                    FROM profiles 
                    WHERE is_bot = 1 AND (photo_id IS NULL OR photo_id = '')
                ''')
                
                bots = []
                for row in cursor.fetchall():
                    bots.append({
                        'user_id': row[0],
                        'name': row[1],
                        'bot_photo_path': row[2]
                    })
                
                return bots
                
        except Exception as e:
            print(f"Error getting bots without photos: {e}")
            return []

    def update_bot_photo_id(self, user_id: int, photo_id: str):
        """Обновить photo_id для бота"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE profiles 
                    SET photo_id = ? 
                    WHERE user_id = ? AND is_bot = 1
                ''', (photo_id, user_id))
                conn.commit()
                
        except Exception as e:
            print(f"Error updating photo_id for bot {user_id}: {e}")

async def main():
    """Главная функция"""
    # Токен бота (нужно вставить реальный токен)
    BOT_TOKEN = "8503492041:AAFHjL8R5jX7Zk9Qm2n3p4o5r6s7t8u9v0w1x2y3z4"
    
    uploader = BotPhotoUploader(BOT_TOKEN)
    stats = await uploader.upload_bot_photos()
    
    print("\nUpload Statistics:")
    print(f"Total bots: {stats['total']}")
    print(f"Uploaded: {stats['uploaded']}")
    print(f"Failed: {stats['failed']}")
    
    if stats['errors']:
        print("\nErrors:")
        for error in stats['errors']:
            print(f"  - {error}")
    
    await uploader.bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
