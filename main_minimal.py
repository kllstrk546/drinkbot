import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Minimal main function for testing"""
    # Get bot token from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    # Initialize bot
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
    @dp.message()
    async def echo_handler(message):
        logger.info(f"Received message: {message.text}")
        await message.answer(f"OK: {message.text}")
    
    logger.info("Minimal bot starting...")
    print("OK: BOT STARTED SUCCESSFULLY!")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"ERROR: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
