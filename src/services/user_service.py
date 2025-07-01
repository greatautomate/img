"""
User service for managing user operations
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from loguru import logger

from ..database import db
from ..models import User, UserStats, ImageEdit, BotAnalytics
from ..config import settings


class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    async def get_or_create_user(telegram_user_id: int, 
                               username: Optional[str] = None,
                               first_name: Optional[str] = None,
                               last_name: Optional[str] = None,
                               language_code: Optional[str] = None) -> Tuple[User, bool]:
        """
        Get existing user or create new one
        
        Args:
            telegram_user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            language_code: User's language code
            
        Returns:
            Tuple of (User object, is_new_user boolean)
        """
        try:
            # Try to get existing user
            user = await db.get_user(telegram_user_id)
            
            if user:
                # Update user info if provided
                updated = False
                if username and user.username != username:
                    user.username = username
                    updated = True
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                if language_code and user.language_code != language_code:
                    user.language_code = language_code
                    updated = True
                
                # Update last seen
                user.update_last_seen()
                
                if updated:
                    await db.update_user(user)
                    logger.info(f"Updated user info for {telegram_user_id}")
                
                return user, False
            
            else:
                # Create new user
                user = User(
                    telegram_user_id=telegram_user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code or "en"
                )
                
                success = await db.create_user(user)
                if success:
                    logger.info(f"Created new user: {telegram_user_id}")
                    
                    # Update analytics
                    await UserService.update_analytics(new_user=True)
                    
                    return user, True
                else:
                    # User might have been created by another process
                    existing_user = await db.get_user(telegram_user_id)
                    if existing_user:
                        return existing_user, False
                    else:
                        raise Exception("Failed to create user")
                        
        except Exception as e:
            logger.error(f"Error getting/creating user {telegram_user_id}: {e}")
            raise
    
    @staticmethod
    async def update_user_stats(telegram_user_id: int, 
                              edit_success: bool = True,
                              edit_type: Optional[str] = None,
                              processing_time: Optional[float] = None) -> bool:
        """
        Update user statistics
        
        Args:
            telegram_user_id: Telegram user ID
            edit_success: Whether the edit was successful
            edit_type: Type of edit performed
            processing_time: Time taken to process edit
            
        Returns:
            True if updated successfully
        """
        try:
            user = await db.get_user(telegram_user_id)
            if not user:
                logger.warning(f"User {telegram_user_id} not found for stats update")
                return False
            
            # Update edit statistics
            user.increment_edit_count(edit_success)
            
            # Add favorite edit type
            if edit_type:
                user.add_favorite_edit_type(edit_type)
            
            # Update user in database
            success = await db.update_user(user)
            
            if success:
                # Update global analytics
                await UserService.update_analytics(
                    edit_success=edit_success,
                    processing_time=processing_time,
                    edit_type=edit_type
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating user stats for {telegram_user_id}: {e}")
            return False
    
    @staticmethod
    async def get_user_statistics(telegram_user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user statistics
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Dictionary with user statistics
        """
        try:
            stats = await db.get_user_stats(telegram_user_id)
            
            if not stats:
                return {
                    "error": "User not found",
                    "total_edits": 0,
                    "successful_edits": 0,
                    "failed_edits": 0,
                    "success_rate": 0.0
                }
            
            # Get recent edits
            recent_edits = await db.get_user_edits(telegram_user_id, limit=5)
            
            # Format statistics
            formatted_stats = {
                "total_edits": stats.get("total_edits", 0),
                "successful_edits": stats.get("successful_edits", 0),
                "failed_edits": stats.get("failed_edits", 0),
                "success_rate": round(stats.get("success_rate", 0.0), 1),
                "recent_edits_this_month": stats.get("recent_edits", 0),
                "favorite_edit_types": stats.get("favorite_edit_types", {}),
                "member_since": stats.get("member_since"),
                "last_seen": stats.get("last_seen"),
                "recent_edits": [
                    {
                        "prompt": edit.prompt[:50] + "..." if len(edit.prompt) > 50 else edit.prompt,
                        "status": edit.status.value,
                        "created_at": edit.created_at,
                        "processing_time": edit.processing_time_seconds
                    }
                    for edit in recent_edits
                ]
            }
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics for {telegram_user_id}: {e}")
            return {"error": "Failed to get statistics"}
    
    @staticmethod
    async def update_analytics(new_user: bool = False,
                             edit_success: bool = True,
                             processing_time: Optional[float] = None,
                             edit_type: Optional[str] = None,
                             aspect_ratio: Optional[str] = None,
                             output_format: Optional[str] = None) -> bool:
        """
        Update global bot analytics
        
        Args:
            new_user: Whether this is a new user
            edit_success: Whether the edit was successful
            processing_time: Time taken to process edit
            edit_type: Type of edit performed
            aspect_ratio: Aspect ratio used
            output_format: Output format used
            
        Returns:
            True if updated successfully
        """
        try:
            analytics = await db.get_or_create_analytics()
            
            analytics.update_stats(
                new_user=new_user,
                edit_success=edit_success,
                processing_time=processing_time,
                edit_type=edit_type,
                aspect_ratio=aspect_ratio,
                output_format=output_format
            )
            
            return await db.update_analytics(analytics)
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
            return False
    
    @staticmethod
    async def get_bot_analytics() -> Dict[str, Any]:
        """
        Get bot analytics summary
        
        Returns:
            Dictionary with bot analytics
        """
        try:
            analytics = await db.get_or_create_analytics()
            return analytics.get_performance_summary()
            
        except Exception as e:
            logger.error(f"Error getting bot analytics: {e}")
            return {"error": "Failed to get analytics"}
    
    @staticmethod
    async def is_user_admin(telegram_user_id: int) -> bool:
        """
        Check if user is an admin
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if user is admin
        """
        return telegram_user_id in settings.admin_user_ids
    
    @staticmethod
    async def ban_user(telegram_user_id: int, admin_id: int) -> bool:
        """
        Ban a user (admin only)
        
        Args:
            telegram_user_id: User to ban
            admin_id: Admin performing the action
            
        Returns:
            True if banned successfully
        """
        try:
            # Check if admin
            if not await UserService.is_user_admin(admin_id):
                logger.warning(f"Non-admin {admin_id} tried to ban user {telegram_user_id}")
                return False
            
            user = await db.get_user(telegram_user_id)
            if not user:
                return False
            
            user.is_banned = True
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            success = await db.update_user(user)
            if success:
                logger.info(f"User {telegram_user_id} banned by admin {admin_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error banning user {telegram_user_id}: {e}")
            return False
    
    @staticmethod
    async def unban_user(telegram_user_id: int, admin_id: int) -> bool:
        """
        Unban a user (admin only)
        
        Args:
            telegram_user_id: User to unban
            admin_id: Admin performing the action
            
        Returns:
            True if unbanned successfully
        """
        try:
            # Check if admin
            if not await UserService.is_user_admin(admin_id):
                logger.warning(f"Non-admin {admin_id} tried to unban user {telegram_user_id}")
                return False
            
            user = await db.get_user(telegram_user_id)
            if not user:
                return False
            
            user.is_banned = False
            user.is_active = True
            user.updated_at = datetime.utcnow()
            
            success = await db.update_user(user)
            if success:
                logger.info(f"User {telegram_user_id} unbanned by admin {admin_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error unbanning user {telegram_user_id}: {e}")
            return False
