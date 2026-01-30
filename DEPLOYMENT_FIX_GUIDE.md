# 🚨 Deployment Fix Guide

## ❌ **ПРОБЛЕМА:**
```
ModuleNotFoundError: No module named 'rotation_check'
```

**Причина:** Файл `rotation_check.py` не был загружен в репозиторий

---

## 🛠️ **РЕШЕНИЕ:**

### **ВАРИАНТ 1: Быстрое исправление (рекомендуется)**

#### **ШАГ 1: Удалите импорт из main.py**
```python
# Удалите эту строку из main.py:
from rotation_check import check_daily_rotation
```

#### **ШАГ 2: Удалите вызов функции**
```python
# Удалите эти строки из main.py:
# Check daily bot rotation
await check_daily_rotation()
```

#### **ШАГ 3: Удалите импорт notification_system**
```python
# Удалите эту строку:
from notification_system import get_notification_system
```

#### **ШАГ 4: Удалите запуск уведомлений**
```python
# Удалите эти строки:
# Initialize and start notification system
notification_system = get_notification_system(bot)
asyncio.create_task(notification_system.start_notification_scheduler())
logger.info("📬 Notification system started")
```

### **ВАРИАНТ 2: Полное исправление**

#### **ШАГ 1: Добавьте недостающие файлы**
Создайте файлы в репозитории:

**rotation_check.py:**
```python
import sqlite3
from datetime import datetime
import random
import logging

async def check_daily_rotation():
    """Check and perform daily bot rotation if needed"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect('drink_bot.db') as conn:
            cursor = conn.cursor()
            
            # Check last rotation date
            cursor.execute('SELECT MAX(date) FROM daily_bot_order')
            last_rotation = cursor.fetchone()[0]
            
            if last_rotation != today:
                logging.info(f"Daily rotation needed! Last: {last_rotation}, Today: {today}")
                
                # Activate all bots for today
                cursor.execute('''
                    UPDATE profiles 
                    SET last_rotation_date = ?
                    WHERE is_bot = 1 AND (last_rotation_date IS NULL OR last_rotation_date != ?)
                ''', (today, today))
                
                activated_count = cursor.rowcount
                logging.info(f"Activated {activated_count} bots for today")
                
                # Delete old orders
                cursor.execute('DELETE FROM daily_bot_order WHERE date != ?', (today,))
                
                # Get all active bots
                cursor.execute('''
                    SELECT user_id, city_normalized, gender
                    FROM profiles 
                    WHERE is_bot = 1 AND last_rotation_date = ?
                    ORDER BY city_normalized, gender, user_id
                ''', (today,))
                
                all_bots = cursor.fetchall()
                
                # Distribute by cities and shuffle
                city_bots = {}
                for user_id, city, gender in all_bots:
                    if city not in city_bots:
                        city_bots[city] = {"male": [], "female": []}
                    city_bots[city][gender].append(user_id)
                
                # Create new order for each city
                total_entries = 0
                for city, bot_lists in city_bots.items():
                    # Shuffle genders separately
                    random.shuffle(bot_lists["male"])
                    random.shuffle(bot_lists["female"])
                    
                    # Interleave genders
                    all_city_bots = []
                    max_len = max(len(bot_lists["male"]), len(bot_lists["female"]))
                    
                    for i in range(max_len):
                        if i < len(bot_lists["male"]):
                            all_city_bots.append(bot_lists["male"][i])
                        if i < len(bot_lists["female"]):
                            all_city_bots.append(bot_lists["female"][i])
                    
                    # Final shuffle for randomness
                    random.shuffle(all_city_bots)
                    
                    # Create daily order entries
                    for order_index, bot_id in enumerate(all_city_bots):
                        cursor.execute('''
                            INSERT INTO daily_bot_order (bot_user_id, city_normalized, date, order_index)
                            VALUES (?, ?, ?, ?)
                        ''', (bot_id, city, today, order_index))
                        total_entries += 1
                
                conn.commit()
                logging.info(f"Daily rotation completed: {total_entries} entries across {len(city_bots)} cities")
                
            else:
                logging.info(f"Daily rotation already up to date for {today}")
                
    except Exception as e:
        logging.error(f"Error in daily rotation check: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
```

**notification_system.py:**
```python
import sqlite3
from datetime import datetime, timedelta
import asyncio
import logging

class NotificationSystem:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'drink_bot.db'
    
    async def update_user_activity(self, user_id: int):
        """Обновить время последней активности пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE profiles 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating user activity: {e}")
    
    async def check_inactive_users(self):
        """Проверить неактивных пользователей и создать уведомления"""
        try:
            now = datetime.now()
            cutoff_24h = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            cutoff_48h = (now - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем неактивных пользователей (24-48 часов)
                cursor.execute('''
                    SELECT user_id, city_normalized, gender FROM profiles 
                    WHERE is_bot = 0 
                    AND last_activity < ?
                    AND last_activity > ?
                ''', (cutoff_24h, cutoff_48h))
                
                inactive_users = cursor.fetchall()
                
                for user_id, city, gender in inactive_users:
                    await self._create_notification(user_id, city, gender)
                
                conn.commit()
                logging.info(f"Processed {len(inactive_users)} inactive users")
                
        except Exception as e:
            logging.error(f"Error checking inactive users: {e}")
    
    async def _create_notification(self, user_id: int, city: str, gender: str):
        """Создать уведомление для пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем количество активных анкет в городе
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT COUNT(*) FROM profiles p
                    JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                    WHERE p.city_normalized = ?
                    AND dbo.date = ?
                    AND p.is_bot = 1
                    AND p.last_rotation_date = ?
                ''', (city, today, today))
                
                active_count = cursor.fetchone()[0]
                
                if active_count > 0:
                    # Определяем текст уведомления
                    if gender == 'male':
                        message = f"📍 Рядом с тобой {active_count} девушек, которые хотят выпить! 🍺\n\nЗаходи в бот и знакомься!"
                    else:
                        message = f"📍 Рядом с тобой {active_count} парней, которые хотят выпить! 🍺\n\nЗаходи в бот и знакомься!"
                    
                    # Проверяем не отправляли ли уже сегодня
                    today_str = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute('''
                        SELECT COUNT(*) FROM user_notifications 
                        WHERE user_id = ? AND notification_type = 'inactive_reminder' 
                        AND DATE(sent_at) = ?
                    ''', (user_id, today_str))
                    
                    if cursor.fetchone()[0] == 0:
                        # Создаем уведомление
                        cursor.execute('''
                            INSERT INTO user_notifications (user_id, notification_type, message)
                            VALUES (?, 'inactive_reminder', ?)
                        ''', (user_id, message))
                        
                        logging.info(f"Created notification for user {user_id} in {city}")
                        
                        # Сразу отправляем
                        await self._send_notification(user_id, message)
                
        except Exception as e:
            logging.error(f"Error creating notification for user {user_id}: {e}")
    
    async def _send_notification(self, user_id: int, message: str):
        """Отправить уведомление пользователю"""
        try:
            await self.bot.send_message(
                user_id,
                message,
                parse_mode='HTML'
            )
            
            # Помечаем как отправленное
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_notifications 
                    SET is_sent = TRUE 
                    WHERE user_id = ? AND message = ?
                ''', (user_id, message))
                conn.commit()
            
            logging.info(f"Sent notification to user {user_id}")
            
        except Exception as e:
            logging.error(f"Error sending notification to user {user_id}: {e}")
    
    async def send_pending_notifications(self):
        """Отправить ожидающие уведомления"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_id, message FROM user_notifications 
                    WHERE is_sent = FALSE
                    ORDER BY sent_at ASC
                    LIMIT 10
                ''')
                
                pending = cursor.fetchall()
                
                for user_id, message in pending:
                    await self._send_notification(user_id, message)
                
                logging.info(f"Sent {len(pending)} pending notifications")
                
        except Exception as e:
            logging.error(f"Error sending pending notifications: {e}")
    
    async def start_notification_scheduler(self):
        """Запустить планировщик уведомлений"""
        while True:
            try:
                # Проверяем неактивных пользователей каждые 6 часов
                await self.check_inactive_users()
                
                # Отправляем ожидающие уведомления каждые 30 минут
                await self.send_pending_notifications()
                
                # Ждем 30 минут
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logging.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

# Глобальная функция для инициализации
notification_system = None

def get_notification_system(bot):
    """Получить экземпляр системы уведомлений"""
    global notification_system
    if notification_system is None:
        notification_system = NotificationSystem(bot)
    return notification_system
```

---

## 🚀 **РЕКОМЕНДЕНДУЕМЫЙ ДЕЙСТВИЯ:**

### **1. Быстрое исправление (5 минут):**
```bash
# В main.py закомментируйте проблемные строки:
# from rotation_check import check_daily_rotation
# from notification_system import get_notification_system

# И закомментируйте вызовы:
# await check_daily_rotation()
# notification_system = get_notification_system(bot)
# asyncio.create_task(notification_system.start_notification_scheduler())
```

### **2. Полное исправление (15 минут):**
```bash
# Добавьте файлы rotation_check.py и notification_system.py в репозиторий
git add rotation_check.py notification_system.py
git commit -m "Add missing rotation and notification files"
git push origin main
```

---

## 🎯 **ЧЕМУ ПРОИЗОШЛО:**

### **Причина:**
- Файлы `rotation_check.py` и `notification_system.py` не были включены в коммит
- Возможно, они были в .gitignore или просто не добавлены

### **Решение:**
- **Быстрое:** Отключить эти функции (бот будет работать без ротации и уведомлений)
- **Полное:** Добавить недостающие файлы

---

## 📞 **ПОДДЕРЖКА:**

### **Если выбрали быстрое исправление:**
- ✅ Бот будет работать
- ⚠️ Без ежедневной ротации
- ⚠️ Без уведомлений

### **Если выбрали полное исправление:**
- ✅ Все фичи будут работать
- ✅ Ежедневная ротация
- ✅ Уведомления

---

## 🎉 **РЕЗУЛЬТАТ:**

**Выберите вариант исправления и примените его. Бот будет работать!** 🚀
