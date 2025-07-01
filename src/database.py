"""
MongoDB database connection and operations
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from loguru import logger

from .config import settings
from .models import User, ImageEdit, BotAnalytics, EditStatus


class Database:
    """MongoDB database manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.users: Optional[AsyncIOMotorCollection] = None
        self.image_edits: Optional[AsyncIOMotorCollection] = None
        self.analytics: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.database_name]
            
            # Initialize collections
            self.users = self.db.users
            self.image_edits = self.db.image_edits
            self.analytics = self.db.analytics
            
            # Create indexes
            await self._create_indexes()
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # User indexes
            await self.users.create_index("telegram_user_id", unique=True)
            await self.users.create_index("username")
            await self.users.create_index("created_at")
            await self.users.create_index("last_seen")
            
            # Image edit indexes
            await self.image_edits.create_index("telegram_user_id")
            await self.image_edits.create_index("user_id")
            await self.image_edits.create_index("status")
            await self.image_edits.create_index("created_at")
            await self.image_edits.create_index("bfl_request_id")
            await self.image_edits.create_index([("telegram_user_id", 1), ("created_at", -1)])
            
            # Analytics indexes
            await self.analytics.create_index("created_at")
            await self.analytics.create_index("updated_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    # User operations
    async def get_user(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID"""
        try:
            user_data = await self.users.find_one({"telegram_user_id": telegram_user_id})
            if user_data:
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get user {telegram_user_id}: {e}")
            return None
    
    async def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            await self.users.insert_one(user.dict(by_alias=True, exclude_unset=True))
            logger.info(f"Created new user: {user.telegram_user_id}")
            return True
        except DuplicateKeyError:
            logger.warning(f"User {user.telegram_user_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create user {user.telegram_user_id}: {e}")
            return False
    
    async def update_user(self, user: User) -> bool:
        """Update an existing user"""
        try:
            result = await self.users.update_one(
                {"telegram_user_id": user.telegram_user_id},
                {"$set": user.dict(by_alias=True, exclude_unset=True)}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user {user.telegram_user_id}: {e}")
            return False
    
    async def get_user_stats(self, telegram_user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            user = await self.get_user(telegram_user_id)
            if not user:
                return {}
            
            # Get recent edits
            recent_edits = await self.image_edits.count_documents({
                "telegram_user_id": telegram_user_id,
                "created_at": {"$gte": datetime.utcnow().replace(day=1)}  # This month
            })
            
            return {
                "total_edits": user.stats.total_edits,
                "successful_edits": user.stats.successful_edits,
                "failed_edits": user.stats.failed_edits,
                "success_rate": user.success_rate,
                "recent_edits": recent_edits,
                "favorite_edit_types": user.stats.favorite_edit_types,
                "member_since": user.created_at,
                "last_seen": user.last_seen
            }
        except Exception as e:
            logger.error(f"Failed to get user stats for {telegram_user_id}: {e}")
            return {}
    
    # Image edit operations
    async def create_image_edit(self, image_edit: ImageEdit) -> bool:
        """Create a new image edit request"""
        try:
            await self.image_edits.insert_one(image_edit.dict(by_alias=True, exclude_unset=True))
            logger.info(f"Created image edit request: {image_edit.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create image edit: {e}")
            return False
    
    async def update_image_edit(self, image_edit: ImageEdit) -> bool:
        """Update an image edit request"""
        try:
            result = await self.image_edits.update_one(
                {"_id": image_edit.id},
                {"$set": image_edit.dict(by_alias=True, exclude_unset=True)}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update image edit {image_edit.id}: {e}")
            return False
    
    async def get_image_edit(self, edit_id: str) -> Optional[ImageEdit]:
        """Get image edit by ID"""
        try:
            edit_data = await self.image_edits.find_one({"_id": edit_id})
            if edit_data:
                return ImageEdit(**edit_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get image edit {edit_id}: {e}")
            return None
    
    async def get_pending_edits(self) -> List[ImageEdit]:
        """Get all pending image edits"""
        try:
            cursor = self.image_edits.find({"status": EditStatus.PENDING})
            edits = []
            async for edit_data in cursor:
                edits.append(ImageEdit(**edit_data))
            return edits
        except Exception as e:
            logger.error(f"Failed to get pending edits: {e}")
            return []
    
    async def get_processing_edits(self) -> List[ImageEdit]:
        """Get all processing image edits"""
        try:
            cursor = self.image_edits.find({"status": EditStatus.PROCESSING})
            edits = []
            async for edit_data in cursor:
                edits.append(ImageEdit(**edit_data))
            return edits
        except Exception as e:
            logger.error(f"Failed to get processing edits: {e}")
            return []
    
    async def get_user_edits(self, telegram_user_id: int, limit: int = 10) -> List[ImageEdit]:
        """Get user's recent image edits"""
        try:
            cursor = self.image_edits.find(
                {"telegram_user_id": telegram_user_id}
            ).sort("created_at", -1).limit(limit)
            
            edits = []
            async for edit_data in cursor:
                edits.append(ImageEdit(**edit_data))
            return edits
        except Exception as e:
            logger.error(f"Failed to get user edits for {telegram_user_id}: {e}")
            return []
    
    # Analytics operations
    async def get_or_create_analytics(self) -> BotAnalytics:
        """Get or create bot analytics"""
        try:
            analytics_data = await self.analytics.find_one()
            if analytics_data:
                return BotAnalytics(**analytics_data)
            else:
                # Create new analytics document
                analytics = BotAnalytics()
                await self.analytics.insert_one(analytics.dict(by_alias=True, exclude_unset=True))
                return analytics
        except Exception as e:
            logger.error(f"Failed to get/create analytics: {e}")
            return BotAnalytics()
    
    async def update_analytics(self, analytics: BotAnalytics) -> bool:
        """Update bot analytics"""
        try:
            result = await self.analytics.update_one(
                {"_id": analytics.id},
                {"$set": analytics.dict(by_alias=True, exclude_unset=True)},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Failed to update analytics: {e}")
            return False


# Global database instance
db = Database()
