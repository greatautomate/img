"""
Tests for service classes
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from src.services import BFLAPIService, ImageProcessor, UserService
from src.models import User, ImageEdit, EditStatus


class TestBFLAPIService:
    """Test BFL.ai API service"""
    
    @pytest.mark.asyncio
    async def test_encode_image_to_base64(self):
        """Test image encoding to base64"""
        image_bytes = b"test_image_data"
        encoded = BFLAPIService.encode_image_to_base64(image_bytes)
        
        assert isinstance(encoded, str)
        assert len(encoded) > 0
    
    def test_validate_image_size(self):
        """Test image size validation"""
        # Valid size
        small_image = b"x" * (5 * 1024 * 1024)  # 5MB
        assert BFLAPIService.validate_image_size(small_image) is True
        
        # Invalid size
        large_image = b"x" * (25 * 1024 * 1024)  # 25MB
        assert BFLAPIService.validate_image_size(large_image) is False
    
    @pytest.mark.asyncio
    async def test_create_edit_request(self):
        """Test creating edit request"""
        service = BFLAPIService()
        
        # Mock the session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "test_request_id",
            "polling_url": "https://api.bfl.ai/v1/results/test_request_id"
        })
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        service.session = mock_session
        
        request_id, polling_url = await service.create_edit_request(
            prompt="Test prompt",
            input_image_base64="fake_base64"
        )
        
        assert request_id == "test_request_id"
        assert polling_url == "https://api.bfl.ai/v1/results/test_request_id"
    
    @pytest.mark.asyncio
    async def test_poll_result(self):
        """Test polling for results"""
        service = BFLAPIService()
        
        # Mock the session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "Ready",
            "result": {"sample": "https://example.com/image.jpg"}
        })
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        service.session = mock_session
        
        result = await service.poll_result("https://api.bfl.ai/v1/results/test")
        
        assert result["status"] == "Ready"
        assert result["result"]["sample"] == "https://example.com/image.jpg"
    
    @pytest.mark.asyncio
    async def test_download_image(self):
        """Test downloading image"""
        service = BFLAPIService()
        
        # Mock the session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake_image_data")
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        service.session = mock_session
        
        image_data = await service.download_image("https://example.com/image.jpg")
        
        assert image_data == b"fake_image_data"


class TestImageProcessor:
    """Test image processor service"""
    
    def test_validate_image_valid(self, sample_image_bytes):
        """Test validating a valid image"""
        with patch('magic.from_buffer', return_value='image/jpeg'), \
             patch('PIL.Image.open') as mock_open:
            
            # Mock PIL Image
            mock_image = MagicMock()
            mock_image.format = "JPEG"
            mock_image.mode = "RGB"
            mock_image.size = (1024, 1024)
            mock_open.return_value = mock_image
            
            result = ImageProcessor.validate_image(sample_image_bytes)
            
            assert result["valid"] is True
            assert result["format"] == "JPEG"
            assert result["size"] == (1024, 1024)
    
    def test_validate_image_too_large(self):
        """Test validating an image that's too large"""
        large_image = b"x" * (25 * 1024 * 1024)  # 25MB
        
        with pytest.raises(Exception) as exc_info:
            ImageProcessor.validate_image(large_image)
        
        assert "too large" in str(exc_info.value).lower()
    
    def test_get_image_info(self, sample_image_bytes):
        """Test getting image information"""
        with patch('PIL.Image.open') as mock_open:
            # Mock PIL Image
            mock_image = MagicMock()
            mock_image.format = "JPEG"
            mock_image.mode = "RGB"
            mock_image.size = (1024, 1024)
            mock_open.return_value = mock_image
            
            info = ImageProcessor.get_image_info(sample_image_bytes)
            
            assert info["format"] == "JPEG"
            assert info["width"] == 1024
            assert info["height"] == 1024
            assert info["pixel_count"] == 1048576
    
    def test_optimize_image(self, sample_image_bytes):
        """Test optimizing an image"""
        with patch('PIL.Image.open') as mock_open, \
             patch('io.BytesIO') as mock_bytesio:
            
            # Mock PIL Image
            mock_image = MagicMock()
            mock_image.mode = "RGB"
            mock_image.size = (1024, 1024)
            mock_image.save = MagicMock()
            mock_open.return_value = mock_image
            
            # Mock BytesIO
            mock_output = MagicMock()
            mock_output.getvalue.return_value = b"optimized_image_data"
            mock_bytesio.return_value = mock_output
            
            result = ImageProcessor.optimize_image(sample_image_bytes)
            
            assert result == b"optimized_image_data"


class TestUserService:
    """Test user service"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, mock_db):
        """Test getting or creating a new user"""
        mock_db.get_user.return_value = None
        mock_db.create_user.return_value = True
        
        with patch('src.services.user_service.db', mock_db):
            user, is_new = await UserService.get_or_create_user(
                telegram_user_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            
            assert is_new is True
            assert user.telegram_user_id == 123456789
            assert user.username == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, mock_db, mock_user):
        """Test getting an existing user"""
        mock_db.get_user.return_value = mock_user
        
        with patch('src.services.user_service.db', mock_db):
            user, is_new = await UserService.get_or_create_user(
                telegram_user_id=123456789
            )
            
            assert is_new is False
            assert user.telegram_user_id == 123456789
    
    @pytest.mark.asyncio
    async def test_update_user_stats(self, mock_db, mock_user):
        """Test updating user statistics"""
        mock_db.get_user.return_value = mock_user
        mock_db.update_user.return_value = True
        
        with patch('src.services.user_service.db', mock_db):
            result = await UserService.update_user_stats(
                telegram_user_id=123456789,
                edit_success=True,
                edit_type="color_change",
                processing_time=30.5
            )
            
            assert result is True
            assert mock_user.stats.total_edits == 1
            assert mock_user.stats.successful_edits == 1
    
    @pytest.mark.asyncio
    async def test_get_user_statistics(self, mock_db):
        """Test getting user statistics"""
        mock_stats = {
            "total_edits": 10,
            "successful_edits": 8,
            "failed_edits": 2,
            "success_rate": 80.0,
            "recent_edits": 5,
            "favorite_edit_types": {"color_change": 5},
            "member_since": "2024-01-01",
            "last_seen": "2024-01-15"
        }
        mock_db.get_user_stats.return_value = mock_stats
        mock_db.get_user_edits.return_value = []
        
        with patch('src.services.user_service.db', mock_db):
            stats = await UserService.get_user_statistics(123456789)
            
            assert stats["total_edits"] == 10
            assert stats["success_rate"] == 80.0
            assert "recent_edits" in stats
    
    @pytest.mark.asyncio
    async def test_is_user_admin(self):
        """Test checking if user is admin"""
        with patch('src.config.settings') as mock_settings:
            mock_settings.admin_user_ids = [123456789, 987654321]
            
            assert await UserService.is_user_admin(123456789) is True
            assert await UserService.is_user_admin(111111111) is False
    
    @pytest.mark.asyncio
    async def test_ban_user(self, mock_db, mock_user):
        """Test banning a user"""
        mock_db.get_user.return_value = mock_user
        mock_db.update_user.return_value = True
        
        with patch('src.services.user_service.UserService.is_user_admin', return_value=True), \
             patch('src.services.user_service.db', mock_db):
            
            result = await UserService.ban_user(
                telegram_user_id=123456789,
                admin_id=987654321
            )
            
            assert result is True
            assert mock_user.is_banned is True
            assert mock_user.is_active is False
    
    @pytest.mark.asyncio
    async def test_ban_user_non_admin(self, mock_db):
        """Test banning a user by non-admin"""
        with patch('src.services.user_service.UserService.is_user_admin', return_value=False), \
             patch('src.services.user_service.db', mock_db):
            
            result = await UserService.ban_user(
                telegram_user_id=123456789,
                admin_id=111111111
            )
            
            assert result is False
