import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database.models import Database
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Инициализация базы данных
db = Database()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    logging.info(f"DEBUG: /start command received from user {user_id}")
    
    # Показываем выбор языка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    
    await message.answer("🌍 Выберите язык / Choose language / Оберіть мову:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def language_selection_callback(callback: CallbackQuery):
    """Обработчик выбора языка"""
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]
    
    logging.info(f"DEBUG: Language selected by user {user_id}: {lang_code}")
    
    # Сохраняем язык в базу данных
    try:
        success = db.update_user_language(user_id, lang_code)
        logging.info(f"DEBUG: Language save result for user {user_id}: {success}")
    except Exception as e:
        logging.error(f"DEBUG: Error saving language for user {user_id}: {e}")
    
    # Ответы на разных языках
    messages = {
        'ru': "✅ Язык изменен на русский! Теперь нажмите кнопку для создания анкеты:",
        'ua': "✅ Мову змінено на українську! Тепер натисніть кнопку для створення анкети:",
        'en': "✅ Language changed to English! Now press the button to create a profile:"
    }
    
    button_texts = {
        'ru': "📝 Заполнить анкету",
        'ua': "📝 Заповнити анкету", 
        'en': "📝 Fill Profile"
    }
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_texts[lang_code])]],
        resize_keyboard=True
    )
    
    await callback.message.answer(messages[lang_code], reply_markup=keyboard)
    await callback.answer("Язык изменен!")

@dp.message(F.text.in_(["📝 Заполнить анкету", "📝 Заповнити анкету", "📝 Fill Profile"]))
async def fill_profile_start(message: Message):
    """Начало заполнения анкеты"""
    user_id = message.from_user.id
    logging.info(f"DEBUG: Fill profile started by user {user_id}")
    
    # Получаем язык пользователя
    try:
        language = db.get_user_language(user_id)
        logging.info(f"DEBUG: User {user_id} language from DB: {language}")
    except Exception as e:
        logging.error(f"DEBUG: Error getting language for user {user_id}: {e}")
        language = 'ru'
    
    prompts = {
        'ru': "📝 Введите ваше имя:",
        'ua': "📝 Введіть ваше ім'я:",
        'en': "📝 Enter your name:"
    }
    
    await message.answer(prompts.get(language, prompts['ru']))

async def main():
    """Главная функция"""
    logging.info("🚀 Starting diagnostic bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
