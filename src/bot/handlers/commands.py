"""
Command handlers for the Telegram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from loguru import logger

from ...config import MESSAGES, BOT_NAME, BOT_VERSION
from ...services import UserService
from ..middleware import UserMiddleware, LoggingMiddleware


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        # Process user through middleware
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        user = context.user_data.get("db_user")
        is_new_user = context.user_data.get("is_new_user", False)
        
        # Create welcome keyboard
        keyboard = [
            [InlineKeyboardButton("📖 Help", callback_data="help")],
            [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = MESSAGES["welcome"]
        if is_new_user:
            welcome_message += "\n\n🎉 **Welcome to the community!** You're now ready to start editing images with AI."
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info(f"Start command processed for user {user.telegram_user_id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, there was an error processing your request. Please try again."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Create help keyboard
        keyboard = [
            [InlineKeyboardButton("🎨 Try Example", callback_data="example")],
            [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
            [InlineKeyboardButton("🔙 Back to Start", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            MESSAGES["help"],
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("⚠️ Error displaying help information.")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        user = context.user_data.get("db_user")
        user_stats = await UserService.get_user_statistics(user.telegram_user_id)
        
        if "error" in user_stats:
            await update.message.reply_text("⚠️ Unable to retrieve your statistics.")
            return
        
        # Format statistics message
        stats_message = f"""
📊 **Your {BOT_NAME} Statistics**

**Overall Performance:**
• Total Edits: {user_stats['total_edits']}
• Successful: {user_stats['successful_edits']} ✅
• Failed: {user_stats['failed_edits']} ❌
• Success Rate: {user_stats['success_rate']}%

**This Month:**
• Recent Edits: {user_stats['recent_edits_this_month']}

**Favorite Edit Types:**
"""
        
        # Add favorite edit types
        favorite_types = user_stats.get('favorite_edit_types', {})
        if favorite_types:
            sorted_types = sorted(favorite_types.items(), key=lambda x: x[1], reverse=True)
            for edit_type, count in sorted_types[:3]:
                stats_message += f"• {edit_type.replace('_', ' ').title()}: {count}\n"
        else:
            stats_message += "• No edits yet\n"
        
        stats_message += f"""
**Account Info:**
• Member Since: {user_stats['member_since'].strftime('%B %Y') if user_stats['member_since'] else 'Unknown'}
• Last Active: {user_stats['last_seen'].strftime('%Y-%m-%d') if user_stats['last_seen'] else 'Unknown'}
        """
        
        # Add recent edits if available
        recent_edits = user_stats.get('recent_edits', [])
        if recent_edits:
            stats_message += "\n**Recent Edits:**\n"
            for edit in recent_edits[:3]:
                status_emoji = "✅" if edit['status'] == 'completed' else "❌" if edit['status'] == 'failed' else "⏳"
                stats_message += f"• {status_emoji} {edit['prompt']}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await update.message.reply_text("⚠️ Error retrieving your statistics.")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        keyboard = [
            [InlineKeyboardButton("🌐 Visit Website", url="https://bfl.ai")],
            [InlineKeyboardButton("📖 Help", callback_data="help")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            MESSAGES["about"],
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in about command: {e}")
        await update.message.reply_text("⚠️ Error displaying about information.")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Clear user context
        context.user_data.clear()
        
        await update.message.reply_text(
            "❌ **Operation Cancelled**\n\n"
            "All pending operations have been cancelled. "
            "You can start fresh by sending a new image or using /start.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in cancel command: {e}")
        await update.message.reply_text("⚠️ Error cancelling operation.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button callbacks"""
    try:
        query = update.callback_query
        await query.answer()
        
        if not await UserMiddleware.process_user(update, context):
            return
        
        callback_data = query.data
        
        if callback_data == "help":
            await help_command(update, context)
        elif callback_data == "stats":
            await stats_command(update, context)
        elif callback_data == "about":
            await about_command(update, context)
        elif callback_data == "start":
            await start_command(update, context)
        elif callback_data == "example":
            await query.edit_message_text(
                "🎨 **Example Usage:**\n\n"
                "1. Send me any image\n"
                "2. Then send a text like:\n"
                "   • 'Change the car color to red'\n"
                "   • 'Replace \"Hello\" with \"Welcome\"'\n"
                "   • 'Add a sunset background'\n"
                "   • 'Remove the person from the image'\n\n"
                "Try it now! Send me an image to get started.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("Unknown command.")
        
    except Exception as e:
        logger.error(f"Error in button callback: {e}")
        try:
            await update.callback_query.answer("⚠️ Error processing request.")
        except:
            pass


async def setup_command_handlers(application, middleware):
    """Setup command handlers"""
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add callback query handler for inline keyboards
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Command handlers setup completed")
    return True
