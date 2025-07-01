"""
Main entry point for MedusaXD AI Image Editor Bot
"""

import asyncio
import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bot import MedusaXDBot
from src.config import settings, BOT_NAME, BOT_VERSION


def setup_logging():
    """Setup logging configuration"""
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file logger
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "medusaxd_bot.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Add error file logger
    logger.add(
        log_dir / "medusaxd_bot_errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="5 MB",
        retention="30 days",
        compression="zip"
    )


def validate_environment():
    """Validate required environment variables"""
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "BFL_API_KEY", 
        "MONGODB_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var.lower(), None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration")
        sys.exit(1)
    
    logger.info("Environment validation passed")


async def main():
    """Main function"""
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Log startup
    logger.info("=" * 60)
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info("=" * 60)
    
    # Validate environment
    validate_environment()
    
    # Create and run bot
    bot = MedusaXDBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await bot.stop()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
