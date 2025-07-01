"""
Main bot class for MedusaXD AI Image Editor Bot
"""

import asyncio
from telegram.ext import Application
from loguru import logger

from ..config import settings, BOT_NAME
from ..database import db
from .handlers import setup_handlers
from .middleware import setup_middleware


class MedusaXDBot:
    """Main bot class"""
    
    def __init__(self):
        self.application: Application = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize the bot"""
        try:
            logger.info(f"Initializing {BOT_NAME}...")
            
            # Connect to database
            await db.connect()
            logger.info("Database connected successfully")
            
            # Create application
            self.application = Application.builder().token(settings.telegram_bot_token).build()
            
            # Setup middleware
            middleware = await setup_middleware(self.application)
            logger.info("Middleware setup completed")
            
            # Setup handlers
            await setup_handlers(self.application, middleware)
            logger.info("Handlers setup completed")
            
            logger.info(f"{BOT_NAME} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    async def start(self):
        """Start the bot"""
        try:
            if not self.application:
                await self.initialize()
            
            logger.info(f"Starting {BOT_NAME}...")
            
            # Initialize application
            await self.application.initialize()
            
            # Start polling
            await self.application.start()
            
            self.is_running = True
            logger.info(f"{BOT_NAME} started successfully and is polling for updates")
            
            # Start polling
            await self.application.updater.start_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot"""
        try:
            logger.info(f"Stopping {BOT_NAME}...")
            
            self.is_running = False
            
            if self.application:
                # Stop polling
                if self.application.updater.running:
                    await self.application.updater.stop()
                
                # Stop application
                await self.application.stop()
                
                # Shutdown application
                await self.application.shutdown()
            
            # Disconnect from database
            await db.disconnect()
            
            logger.info(f"{BOT_NAME} stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    async def restart(self):
        """Restart the bot"""
        logger.info(f"Restarting {BOT_NAME}...")
        await self.stop()
        await asyncio.sleep(2)
        await self.start()
    
    def get_bot_info(self):
        """Get bot information"""
        return {
            "name": BOT_NAME,
            "username": settings.bot_username,
            "environment": settings.environment,
            "is_running": self.is_running,
            "database_connected": db.client is not None
        }


async def run_bot():
    """Run the bot (main entry point)"""
    bot = MedusaXDBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping bot...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Run the bot
    asyncio.run(run_bot())
