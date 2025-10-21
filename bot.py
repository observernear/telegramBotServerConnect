import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.config import config
from handlers.start import router as start_router
from handlers.commands import router as commands_router
from handlers.terminal import router as terminal_router
from services.ssh_client import ssh_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function"""
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Include routers
    dp.include_router(start_router)
    dp.include_router(terminal_router)
    dp.include_router(commands_router)
    
    # Test SSH connection on startup
    try:
        logger.info("Testing SSH connection...")
        success = await ssh_client.connect()
        if success:
            logger.info("SSH connection test successful")
        else:
            logger.error("SSH connection test failed")
    except Exception as e:
        logger.error(f"SSH connection test error: {e}")
    
    # Start polling
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Cleanup
        await ssh_client.close_all_sessions()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())