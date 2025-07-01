"""
Middleware for Telegram bot
"""

import time
from typing import Dict, Any, Callable, Awaitable
from telegram import Update
from telegram.ext import ContextTypes, BaseHandler
from loguru import logger

from ..services import UserService
from ..config import settings


class UserMiddleware:
    """Middleware to handle user registration and updates"""
    
    @staticmethod
    async def process_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process user information and ensure user exists in database"""
        if not update.effective_user:
            return
        
        telegram_user = update.effective_user
        
        try:
            # Get or create user
            user, is_new = await UserService.get_or_create_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code
            )
            
            # Store user in context for handlers
            context.user_data["db_user"] = user
            context.user_data["is_new_user"] = is_new
            
            # Check if user is banned
            if user.is_banned:
                await update.message.reply_text(
                    "❌ Your account has been suspended. Contact support for assistance."
                )
                return False  # Stop processing
            
            if is_new:
                logger.info(f"New user registered: {user.full_name} ({telegram_user.id})")
            
        except Exception as e:
            logger.error(f"Error processing user {telegram_user.id}: {e}")
            await update.message.reply_text(
                "⚠️ There was an error processing your request. Please try again later."
            )
            return False
        
        return True


class RateLimitMiddleware:
    """Middleware for rate limiting (if needed in future)"""
    
    def __init__(self):
        self.user_requests: Dict[int, list] = {}
        self.max_requests_per_minute = 10
    
    async def check_rate_limit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is within rate limits"""
        if not update.effective_user:
            return True
        
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if current_time - req_time < 60
            ]
        else:
            self.user_requests[user_id] = []
        
        # Check if user exceeded rate limit
        if len(self.user_requests[user_id]) >= self.max_requests_per_minute:
            await update.message.reply_text(
                "⏰ You're sending requests too quickly. Please wait a moment and try again."
            )
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True


class LoggingMiddleware:
    """Middleware for logging user interactions"""
    
    @staticmethod
    async def log_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log user interactions for analytics"""
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id
        username = update.effective_user.username or "N/A"
        message_type = "text"
        
        if update.message.photo:
            message_type = "photo"
        elif update.message.document:
            message_type = "document"
        elif update.message.voice:
            message_type = "voice"
        
        logger.info(
            f"User interaction - ID: {user_id}, Username: @{username}, "
            f"Type: {message_type}, Text: {update.message.text[:50] if update.message.text else 'N/A'}"
        )


class ErrorHandlingMiddleware:
    """Middleware for error handling"""
    
    @staticmethod
    async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle errors gracefully"""
        logger.error(f"Error in bot handler: {error}", exc_info=True)
        
        if update and update.message:
            try:
                await update.message.reply_text(
                    "⚠️ An unexpected error occurred. Our team has been notified. "
                    "Please try again in a few moments."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")


async def setup_middleware(application):
    """Setup all middleware for the bot"""
    
    # Create middleware instances
    user_middleware = UserMiddleware()
    rate_limit_middleware = RateLimitMiddleware()
    logging_middleware = LoggingMiddleware()
    error_middleware = ErrorHandlingMiddleware()
    
    # Add error handler
    application.add_error_handler(error_middleware.handle_error)
    
    logger.info("Middleware setup completed")
    
    return {
        "user_middleware": user_middleware,
        "rate_limit_middleware": rate_limit_middleware,
        "logging_middleware": logging_middleware,
        "error_middleware": error_middleware
    }
