"""
Main entry point for the Telegram bot
"""
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Import configuration
from config import Config

# Import database
from database.connection import db_manager

# Import handlers
from handlers.admin import admin_router
from handlers.user import user_router
from handlers.member import member_router
from handlers.callback import callback_router

async def init_database():
    """Initialize database connection"""
    try:
        success = await db_manager.connect()
        if not success:
            logger.error("Failed to initialize database")
            return False
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

async def cleanup_old_conversations():
    """Periodic cleanup of old conversation history"""
    try:
        from database.queries import DatabaseQueries
        await DatabaseQueries.cleanup_old_conversations(days_old=7)
        logger.info("Old conversation history cleaned up")
    except Exception as e:
        logger.error(f"Error during conversation cleanup: {e}")

async def periodic_cleanup():
    """Run periodic cleanup tasks"""
    while True:
        try:
            # Wait 24 hours
            await asyncio.sleep(24 * 60 * 60)
            await cleanup_old_conversations()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

async def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Configure logging
        logger.remove()
        logger.add(
            sys.stderr,
            level=Config.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            "logs/bot.log",
            rotation="1 day",
            retention="30 days",
            level=Config.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
        
        # Initialize database
        if not await init_database():
            logger.error("Failed to initialize database. Exiting.")
            return
        
        # Initialize bot and dispatcher
        bot = Bot(
            token=Config.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        
        # Register startup handler
        async def on_startup():
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Bot webhook cleared and ready for polling")
        
        dp.startup.register(on_startup)
        
        # Register routers
        dp.include_router(admin_router)
        dp.include_router(member_router)
        dp.include_router(callback_router)
        dp.include_router(user_router)  # User router should be last to catch all other messages
        
        logger.info("Bot routers registered successfully")
        
        # Start periodic cleanup task
        cleanup_task = asyncio.create_task(periodic_cleanup())
        
        # Start polling with chat member updates enabled
        logger.info("Starting bot polling...")
        try:
            await dp.start_polling(
                bot,
                allowed_updates=["message", "chat_member", "callback_query", "my_chat_member"]
            )
        finally:
            cleanup_task.cancel()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        raise
    finally:
        # Cleanup
        try:
            await db_manager.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)