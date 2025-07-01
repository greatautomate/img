"""
Tests for database operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from src.database import Database
from src.models import User, ImageEdit, BotAnalytics, EditStatus


class TestDatabase:
    """Test database operations"""
    
    @pytest.fixture
    async def db_instance(self):
        """Create a test database instance"""
        db = Database()
        
        # Mock the client and collections
        db.client = AsyncMock()
        db.db = MagicMock()
        db.users = AsyncMock()
        db.image_edits = AsyncMock()
        db.analytics = AsyncMock()
        
        return db
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test database connection"""
        db = Database()
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_client.return_value.admin.command = AsyncMock()
            
            await db.connect()
            
            assert db.client is not None
            mock_client.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_exists(self, db_instance, mock_user):
        """Test getting an existing user"""
        db_instance.users.find_one.return_value = mock_user.dict(by_alias=True)
        
        result = await db_instance.get_user(123456789)
        
        assert result is not None
        assert result.telegram_user_id == 123456789
        db_instance.users.find_one.assert_called_once_with({"telegram_user_id": 123456789})
    
    @pytest.mark.asyncio
    async def test_get_user_not_exists(self, db_instance):
        """Test getting a non-existent user"""
        db_instance.users.find_one.return_value = None
        
        result = await db_instance.get_user(123456789)
        
        assert result is None
        db_instance.users.find_one.assert_called_once_with({"telegram_user_id": 123456789})
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_instance, mock_user):
        """Test creating a user successfully"""
        db_instance.users.insert_one.return_value = None
        
        result = await db_instance.create_user(mock_user)
        
        assert result is True
        db_instance.users.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, db_instance, mock_user):
        """Test creating a duplicate user"""
        from pymongo.errors import DuplicateKeyError
        
        db_instance.users.insert_one.side_effect = DuplicateKeyError("Duplicate key")
        
        result = await db_instance.create_user(mock_user)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, db_instance, mock_user):
        """Test updating a user successfully"""
        mock_result = MagicMock()
        mock_result.modified_count = 1
        db_instance.users.update_one.return_value = mock_result
        
        result = await db_instance.update_user(mock_user)
        
        assert result is True
        db_instance.users.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_no_changes(self, db_instance, mock_user):
        """Test updating a user with no changes"""
        mock_result = MagicMock()
        mock_result.modified_count = 0
        db_instance.users.update_one.return_value = mock_result
        
        result = await db_instance.update_user(mock_user)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_image_edit_success(self, db_instance, mock_image_edit):
        """Test creating an image edit successfully"""
        db_instance.image_edits.insert_one.return_value = None
        
        result = await db_instance.create_image_edit(mock_image_edit)
        
        assert result is True
        db_instance.image_edits.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_image_edit_success(self, db_instance, mock_image_edit):
        """Test updating an image edit successfully"""
        mock_result = MagicMock()
        mock_result.modified_count = 1
        db_instance.image_edits.update_one.return_value = mock_result
        
        result = await db_instance.update_image_edit(mock_image_edit)
        
        assert result is True
        db_instance.image_edits.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_edits(self, db_instance):
        """Test getting pending edits"""
        mock_edit_data = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "telegram_user_id": 123456789,
            "telegram_message_id": 12345,
            "prompt": "Test prompt",
            "status": "pending"
        }
        
        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [mock_edit_data]
        db_instance.image_edits.find.return_value = mock_cursor
        
        result = await db_instance.get_pending_edits()
        
        assert len(result) == 1
        assert result[0].status == EditStatus.PENDING
        db_instance.image_edits.find.assert_called_once_with({"status": EditStatus.PENDING})
    
    @pytest.mark.asyncio
    async def test_get_processing_edits(self, db_instance):
        """Test getting processing edits"""
        mock_edit_data = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "telegram_user_id": 123456789,
            "telegram_message_id": 12345,
            "prompt": "Test prompt",
            "status": "processing"
        }
        
        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [mock_edit_data]
        db_instance.image_edits.find.return_value = mock_cursor
        
        result = await db_instance.get_processing_edits()
        
        assert len(result) == 1
        assert result[0].status == EditStatus.PROCESSING
        db_instance.image_edits.find.assert_called_once_with({"status": EditStatus.PROCESSING})
    
    @pytest.mark.asyncio
    async def test_get_user_edits(self, db_instance):
        """Test getting user edits"""
        mock_edit_data = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "telegram_user_id": 123456789,
            "telegram_message_id": 12345,
            "prompt": "Test prompt",
            "status": "completed"
        }
        
        # Mock cursor with sort and limit
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = [mock_edit_data]
        db_instance.image_edits.find.return_value = mock_cursor
        
        result = await db_instance.get_user_edits(123456789, limit=5)
        
        assert len(result) == 1
        assert result[0].telegram_user_id == 123456789
        db_instance.image_edits.find.assert_called_once_with({"telegram_user_id": 123456789})
    
    @pytest.mark.asyncio
    async def test_get_or_create_analytics_existing(self, db_instance):
        """Test getting existing analytics"""
        mock_analytics_data = {
            "_id": ObjectId(),
            "total_users": 100,
            "total_edits": 500,
            "successful_edits": 450,
            "failed_edits": 50
        }
        
        db_instance.analytics.find_one.return_value = mock_analytics_data
        
        result = await db_instance.get_or_create_analytics()
        
        assert result.total_users == 100
        assert result.total_edits == 500
        db_instance.analytics.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_analytics_new(self, db_instance):
        """Test creating new analytics"""
        db_instance.analytics.find_one.return_value = None
        db_instance.analytics.insert_one.return_value = None
        
        result = await db_instance.get_or_create_analytics()
        
        assert result.total_users == 0
        assert result.total_edits == 0
        db_instance.analytics.find_one.assert_called_once()
        db_instance.analytics.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_analytics_success(self, db_instance):
        """Test updating analytics successfully"""
        analytics = BotAnalytics()
        
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        db_instance.analytics.update_one.return_value = mock_result
        
        result = await db_instance.update_analytics(analytics)
        
        assert result is True
        db_instance.analytics.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self, db_instance, mock_user):
        """Test getting user statistics"""
        db_instance.get_user.return_value = mock_user
        db_instance.image_edits.count_documents.return_value = 5
        
        result = await db_instance.get_user_stats(123456789)
        
        assert "total_edits" in result
        assert "success_rate" in result
        assert "recent_edits" in result
        db_instance.get_user.assert_called_once_with(123456789)
