"""
Tests for database models
"""

import pytest
from datetime import datetime
from bson import ObjectId

from src.models import User, UserStats, ImageEdit, EditStatus, BotAnalytics


class TestUser:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User(
            telegram_user_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        
        assert user.telegram_user_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.is_banned is False
        assert isinstance(user.stats, UserStats)
    
    def test_user_full_name(self):
        """Test user full name property"""
        # Test with first and last name
        user = User(
            telegram_user_id=123456789,
            first_name="Test",
            last_name="User"
        )
        assert user.full_name == "Test User"
        
        # Test with only first name
        user = User(
            telegram_user_id=123456789,
            first_name="Test"
        )
        assert user.full_name == "Test"
        
        # Test with only username
        user = User(
            telegram_user_id=123456789,
            username="test_user"
        )
        assert user.full_name == "@test_user"
        
        # Test with no name info
        user = User(telegram_user_id=123456789)
        assert user.full_name == "User 123456789"
    
    def test_user_success_rate(self):
        """Test user success rate calculation"""
        user = User(telegram_user_id=123456789)
        
        # No edits
        assert user.success_rate == 0.0
        
        # With edits
        user.stats.total_edits = 10
        user.stats.successful_edits = 8
        assert user.success_rate == 80.0
    
    def test_increment_edit_count(self):
        """Test incrementing edit count"""
        user = User(telegram_user_id=123456789)
        
        # Successful edit
        user.increment_edit_count(success=True)
        assert user.stats.total_edits == 1
        assert user.stats.successful_edits == 1
        assert user.stats.failed_edits == 0
        
        # Failed edit
        user.increment_edit_count(success=False)
        assert user.stats.total_edits == 2
        assert user.stats.successful_edits == 1
        assert user.stats.failed_edits == 1
    
    def test_add_favorite_edit_type(self):
        """Test adding favorite edit types"""
        user = User(telegram_user_id=123456789)
        
        user.add_favorite_edit_type("color_change")
        assert user.stats.favorite_edit_types["color_change"] == 1
        
        user.add_favorite_edit_type("color_change")
        assert user.stats.favorite_edit_types["color_change"] == 2
        
        user.add_favorite_edit_type("text_edit")
        assert user.stats.favorite_edit_types["text_edit"] == 1


class TestImageEdit:
    """Test ImageEdit model"""
    
    def test_image_edit_creation(self):
        """Test creating an image edit"""
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Change the car color to red"
        )
        
        assert edit.telegram_user_id == 123456789
        assert edit.prompt == "Change the car color to red"
        assert edit.status == EditStatus.PENDING
        assert edit.retry_count == 0
    
    def test_start_processing(self):
        """Test starting processing"""
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Test prompt"
        )
        
        edit.start_processing("test_id", "test_url")
        
        assert edit.status == EditStatus.PROCESSING
        assert edit.bfl_request_id == "test_id"
        assert edit.bfl_polling_url == "test_url"
        assert edit.started_at is not None
    
    def test_complete_successfully(self):
        """Test successful completion"""
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Test prompt"
        )
        
        edit.start_processing("test_id", "test_url")
        edit.complete_successfully("https://example.com/image.jpg")
        
        assert edit.status == EditStatus.COMPLETED
        assert edit.edited_image_url == "https://example.com/image.jpg"
        assert edit.completed_at is not None
        assert edit.processing_time_seconds is not None
        assert edit.is_successful is True
    
    def test_fail_with_error(self):
        """Test failing with error"""
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Test prompt"
        )
        
        edit.start_processing("test_id", "test_url")
        edit.fail_with_error("Test error")
        
        assert edit.status == EditStatus.FAILED
        assert edit.error_message == "Test error"
        assert edit.completed_at is not None
        assert edit.is_successful is False
    
    def test_classify_edit_type(self):
        """Test edit type classification"""
        # Text edit
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Replace 'Hello' with 'Welcome'"
        )
        assert edit.classify_edit_type() == "text_edit"
        
        # Color change
        edit.prompt = "Change the car color to red"
        assert edit.classify_edit_type() == "color_change"
        
        # Object modification
        edit.prompt = "Remove the person from the image"
        assert edit.classify_edit_type() == "object_modification"
        
        # Background change
        edit.prompt = "Add a sunset background"
        assert edit.classify_edit_type() == "background_change"
        
        # General edit
        edit.prompt = "Make it look better"
        assert edit.classify_edit_type() == "general_edit"
    
    def test_can_retry(self):
        """Test retry logic"""
        edit = ImageEdit(
            user_id=ObjectId(),
            telegram_user_id=123456789,
            telegram_message_id=12345,
            prompt="Test prompt"
        )
        
        # Failed edit with retries available
        edit.fail_with_error("Test error")
        assert edit.can_retry() is True
        
        # Exceed max retries
        edit.retry_count = 3
        assert edit.can_retry() is False
        
        # Successful edit
        edit.complete_successfully("test_url")
        assert edit.can_retry() is False


class TestBotAnalytics:
    """Test BotAnalytics model"""
    
    def test_analytics_creation(self):
        """Test creating analytics"""
        analytics = BotAnalytics()
        
        assert analytics.total_users == 0
        assert analytics.total_edits == 0
        assert analytics.success_rate == 0.0
        assert len(analytics.daily_stats) == 0
    
    def test_update_stats(self):
        """Test updating statistics"""
        analytics = BotAnalytics()
        
        # Add new user and successful edit
        analytics.update_stats(
            new_user=True,
            edit_success=True,
            processing_time=30.5,
            edit_type="color_change"
        )
        
        assert analytics.total_users == 1
        assert analytics.total_edits == 1
        assert analytics.successful_edits == 1
        assert analytics.success_rate == 100.0
        assert analytics.average_processing_time == 30.5
        assert analytics.popular_edit_types["color_change"] == 1
        assert len(analytics.daily_stats) == 1
    
    def test_get_top_edit_types(self):
        """Test getting top edit types"""
        analytics = BotAnalytics()
        
        # Add some edit types
        analytics.popular_edit_types = {
            "color_change": 10,
            "text_edit": 5,
            "background_change": 8,
            "object_modification": 3
        }
        
        top_types = analytics.get_top_edit_types(limit=3)
        
        assert len(top_types) == 3
        assert top_types[0] == ("color_change", 10)
        assert top_types[1] == ("background_change", 8)
        assert top_types[2] == ("text_edit", 5)
    
    def test_get_performance_summary(self):
        """Test getting performance summary"""
        analytics = BotAnalytics()
        analytics.total_users = 100
        analytics.total_edits = 500
        analytics.successful_edits = 450
        analytics.success_rate = 90.0
        analytics.average_processing_time = 25.5
        
        summary = analytics.get_performance_summary()
        
        assert summary["total_users"] == 100
        assert summary["total_edits"] == 500
        assert summary["success_rate"] == 90.0
        assert summary["average_processing_time"] == 25.5
        assert "top_edit_types" in summary
        assert "last_updated" in summary
