"""
Admin handlers for the Telegram bot
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from loguru import logger

from ...services import UserService
from ...database import db
from ..middleware import UserMiddleware, LoggingMiddleware


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_stats command (admin only)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        user = context.user_data.get("db_user")
        
        # Check if user is admin
        if not await UserService.is_user_admin(user.telegram_user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Get bot analytics
        analytics = await UserService.get_bot_analytics()
        
        if "error" in analytics:
            await update.message.reply_text("⚠️ Error retrieving analytics.")
            return
        
        # Format analytics message
        stats_message = f"""
🔧 **Admin Dashboard - Bot Analytics**

**Overall Statistics:**
• Total Users: {analytics['total_users']:,}
• Total Edits: {analytics['total_edits']:,}
• Success Rate: {analytics['success_rate']}%
• Avg Processing Time: {analytics['average_processing_time']}s

**Top Edit Types:**
"""
        
        for edit_type, count in analytics['top_edit_types']:
            stats_message += f"• {edit_type.replace('_', ' ').title()}: {count:,}\n"
        
        stats_message += f"\n**Last Updated:** {analytics['last_updated'].strftime('%Y-%m-%d %H:%M UTC')}"
        
        await update.message.reply_text(
            stats_message,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in admin stats command: {e}")
        await update.message.reply_text("⚠️ Error retrieving admin statistics.")


async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command (admin only)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        user = context.user_data.get("db_user")
        
        # Check if user is admin
        if not await UserService.is_user_admin(user.telegram_user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Get user ID to ban from command arguments
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ **Usage:** `/ban <user_id>`\n\n"
                "Example: `/ban 123456789`",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Must be a number.")
            return
        
        # Ban user
        success = await UserService.ban_user(target_user_id, user.telegram_user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ **User Banned**\n\n"
                f"User ID `{target_user_id}` has been banned.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ **Ban Failed**\n\n"
                f"Could not ban user ID `{target_user_id}`. User may not exist.",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error in ban user command: {e}")
        await update.message.reply_text("⚠️ Error processing ban command.")


async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command (admin only)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        user = context.user_data.get("db_user")
        
        # Check if user is admin
        if not await UserService.is_user_admin(user.telegram_user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Get user ID to unban from command arguments
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ **Usage:** `/unban <user_id>`\n\n"
                "Example: `/unban 123456789`",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Must be a number.")
            return
        
        # Unban user
        success = await UserService.unban_user(target_user_id, user.telegram_user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ **User Unbanned**\n\n"
                f"User ID `{target_user_id}` has been unbanned.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ **Unban Failed**\n\n"
                f"Could not unban user ID `{target_user_id}`. User may not exist.",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error in unban user command: {e}")
        await update.message.reply_text("⚠️ Error processing unban command.")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command (admin only)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        user = context.user_data.get("db_user")
        
        # Check if user is admin
        if not await UserService.is_user_admin(user.telegram_user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        # Get broadcast message from command arguments
        if not context.args:
            await update.message.reply_text(
                "❌ **Usage:** `/broadcast <message>`\n\n"
                "Example: `/broadcast Important update: Bot will be down for maintenance.`",
                parse_mode="Markdown"
            )
            return
        
        broadcast_message = " ".join(context.args)
        
        await update.message.reply_text(
            "📢 **Broadcast Feature**\n\n"
            "Broadcast functionality would be implemented here.\n"
            f"**Message:** {broadcast_message}\n\n"
            "⚠️ This is a placeholder - implement actual broadcast logic as needed.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await update.message.reply_text("⚠️ Error processing broadcast command.")


async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_help command (admin only)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        user = context.user_data.get("db_user")
        
        # Check if user is admin
        if not await UserService.is_user_admin(user.telegram_user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        help_message = """
🔧 **Admin Commands Help**

**Analytics & Monitoring:**
• `/admin_stats` - View bot analytics and statistics

**User Management:**
• `/ban <user_id>` - Ban a user from using the bot
• `/unban <user_id>` - Unban a previously banned user

**Communication:**
• `/broadcast <message>` - Send message to all users (placeholder)

**General:**
• `/admin_help` - Show this help message

**Notes:**
• All admin commands are logged
• User IDs can be found in bot logs
• Use admin commands responsibly
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in admin help command: {e}")
        await update.message.reply_text("⚠️ Error displaying admin help.")


async def setup_admin_handlers(application, middleware):
    """Setup admin command handlers"""
    
    # Add admin command handlers
    application.add_handler(CommandHandler("admin_stats", admin_stats_command))
    application.add_handler(CommandHandler("ban", ban_user_command))
    application.add_handler(CommandHandler("unban", unban_user_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("admin_help", admin_help_command))
    
    logger.info("Admin handlers setup completed")
    return True
