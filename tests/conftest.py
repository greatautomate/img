"""
Pytest configuration and fixtures for MedusaXD AI Image Editor Bot tests
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["BFL_API_KEY"] = "test_api_key"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/test_medusaxd_bot"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Mock database for testing"""
    from src.database import db
    
    # Mock the database methods
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.get_user = AsyncMock()
    db.create_user = AsyncMock(return_value=True)
    db.update_user = AsyncMock(return_value=True)
    db.create_image_edit = AsyncMock(return_value=True)
    db.update_image_edit = AsyncMock(return_value=True)
    db.get_or_create_analytics = AsyncMock()
    db.update_analytics = AsyncMock(return_value=True)
    
    yield db


@pytest.fixture
def mock_user():
    """Mock user for testing"""
    from src.models import User, UserStats
    
    return User(
        telegram_user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en",
        stats=UserStats()
    )


@pytest.fixture
def mock_image_edit():
    """Mock image edit for testing"""
    from src.models import ImageEdit, EditStatus
    
    return ImageEdit(
        user_id="507f1f77bcf86cd799439011",
        telegram_user_id=123456789,
        telegram_message_id=12345,
        prompt="Change the car color to red",
        status=EditStatus.PENDING
    )


@pytest.fixture
def mock_bfl_service():
    """Mock BFL.ai API service for testing"""
    from src.services import BFLAPIService
    
    service = MagicMock(spec=BFLAPIService)
    service.create_edit_request = AsyncMock(return_value=("test_id", "test_url"))
    service.wait_for_completion = AsyncMock(return_value={
        "status": "Ready",
        "result": {"sample": "https://example.com/edited_image.jpg"}
    })
    service.download_image = AsyncMock(return_value=b"fake_image_data")
    service.encode_image_to_base64 = MagicMock(return_value="fake_base64")
    service.validate_image_size = MagicMock(return_value=True)
    
    return service


@pytest.fixture
def mock_telegram_update():
    """Mock Telegram update for testing"""
    from telegram import Update, Message, User as TelegramUser, Chat, PhotoSize
    
    # Create mock objects
    telegram_user = TelegramUser(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="test_user"
    )
    
    chat = Chat(id=123456789, type="private")
    
    message = Message(
        message_id=12345,
        date=datetime.utcnow(),
        chat=chat,
        from_user=telegram_user,
        text="Test message"
    )
    
    update = Update(update_id=1, message=message)
    
    return update


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram context for testing"""
    from telegram.ext import ContextTypes
    
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    
    return context


@pytest.fixture
def sample_image_bytes():
    """Sample image bytes for testing"""
    # Create a minimal valid JPEG header
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
    jpeg_footer = b'\xff\xd9'
    
    # Create fake image data
    fake_image_data = jpeg_header + b'\x00' * 100 + jpeg_footer
    
    return fake_image_data


@pytest.fixture
def mock_image_processor():
    """Mock image processor for testing"""
    from src.services import ImageProcessor
    
    processor = MagicMock(spec=ImageProcessor)
    processor.validate_image = MagicMock(return_value={
        "valid": True,
        "format": "JPEG",
        "mode": "RGB",
        "size": (1024, 1024),
        "pixel_count": 1048576,
        "file_size_mb": 0.5,
        "mime_type": "image/jpeg"
    })
    processor.optimize_image = MagicMock(return_value=b"optimized_image_data")
    processor.get_image_info = MagicMock(return_value={
        "format": "JPEG",
        "size": (1024, 1024),
        "file_size_mb": 0.5
    })
    
    return processor


@pytest.fixture
def mock_user_service():
    """Mock user service for testing"""
    from src.services import UserService
    
    service = MagicMock(spec=UserService)
    service.get_or_create_user = AsyncMock()
    service.update_user_stats = AsyncMock(return_value=True)
    service.get_user_statistics = AsyncMock(return_value={
        "total_edits": 10,
        "successful_edits": 8,
        "failed_edits": 2,
        "success_rate": 80.0
    })
    service.is_user_admin = AsyncMock(return_value=False)
    
    return service


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Ensure test environment is set
    os.environ["ENVIRONMENT"] = "test"
    
    yield
    
    # Cleanup after test
    pass
