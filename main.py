import asyncio
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.start import router

# Load environment variables
load_dotenv()

# Configure advanced logging
def setup_logging():
    """Setup advanced logging with DEBUG level and detailed formatting"""
    
    # Create custom formatter with detailed information
    class DetailedFormatter(logging.Formatter):
        def format(self, record):
            # Add timestamp, level, module, line number
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            module = record.module if hasattr(record, 'module') else 'unknown'
            line = record.lineno if hasattr(record, 'lineno') else 'unknown'
            
            # Format the base message
            base_msg = f"{timestamp} - {record.levelname:8} - {module}:{line} - {record.getMessage()}"
            
            # Add exception info if present
            if record.exc_info:
                base_msg += f"\nEXCEPTION: {self.formatException(record.exc_info)}"
            
            # Add extra fields if present
            if hasattr(record, 'user_id'):
                base_msg += f" [USER:{record.user_id}]"
            if hasattr(record, 'step'):
                base_msg += f" [STEP:{record.step}]"
            if hasattr(record, 'query'):
                base_msg += f" [QUERY:{record.query}]"
                
            return base_msg
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Enable DEBUG level
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with detailed formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(DetailedFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger('aiogram').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.INFO)  # Reduce asyncio noise
    
    logging.info("=" * 60)
    logging.info("🚀 DRINK BOT STARTING - ADVANCED LOGGING ENABLED")
    logging.info("=" * 60)
    
    return root_logger

# Clean database on start for fresh testing
# Temporarily disabled due to permission issues
# if os.path.exists("drink_bot.db"):
#     os.remove("drink_bot.db")
#     print("🗑️ Database cleaned for fresh start")

# Configure logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Middleware for logging all updates
async def log_updates(handler, event, data):
    """Log all incoming updates and user states"""
    try:
        if event.message:
            user_id = event.message.from_user.id
            text = event.message.text or f"[{event.message.content_type}]"
            logger.debug(f"MESSAGE from {user_id}: {text}")
            
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            callback_data = event.callback_query.data
            logger.debug(f"CALLBACK from {user_id}: {callback_data}")
            
    except Exception as e:
        logger.error(f"Logging middleware error: {e}")
    
    return await handler(event, data)

async def main():
    """Main function to run the bot"""
    # Setup advanced logging first
    logger = setup_logging()
    
    # Get bot token from environment variables
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with BOT_TOKEN=your_token_here")
        return
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Set bot instance for notifications
        from handlers.start import set_bot_instance
        set_bot_instance(bot)
        
        # Initialize dispatcher with memory storage for FSM
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Add logging middleware
        dp.update.middleware(log_updates)
        
        # Include routers - REGISTRATION FIRST!
        dp.include_router(router)  # Registration router must be first
        
        logger.info("📋 Registration router included FIRST")
        logger.info("🚀 Starting bot...")
        
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 CRITICAL BOT ERROR: {e}")
        import traceback
        logger.error(f"💥 TRACEBACK: {traceback.format_exc()}")
    finally:
        if 'bot' in locals():
            await bot.session.close()
            logger.info("🔌 Bot session closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 FATAL ERROR: {e}")
        import traceback
        print(f"💥 TRACEBACK: {traceback.format_exc()}")
