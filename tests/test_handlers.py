"""
Tests for bot handlers
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.commands import start_command, help_command, stats_command
from src.bot.handlers.messages import handle_photo, handle_text
from src.models import User, UserStats


class TestCommandHandlers:
    """Test command handlers"""
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_telegram_update, mock_telegram_context, mock_user):
        """Test /start command"""
        mock_telegram_context.user_data = {
            "db_user": mock_user,
            "is_new_user": True
        }
        
        with patch('src.bot.handlers.commands.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.commands.LoggingMiddleware.log_interaction'):
            
            await start_command(mock_telegram_update, mock_telegram_context)
            
            # Check that reply_text was called
            mock_telegram_update.message.reply_text.assert_called_once()
            
            # Check that the message contains welcome text
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "Welcome" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_telegram_update, mock_telegram_context):
        """Test /help command"""
        with patch('src.bot.handlers.commands.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.commands.LoggingMiddleware.log_interaction'):
            
            await help_command(mock_telegram_update, mock_telegram_context)
            
            # Check that reply_text was called
            mock_telegram_update.message.reply_text.assert_called_once()
            
            # Check that the message contains help text
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "Help" in call_args[0][0] or "help" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_stats_command(self, mock_telegram_update, mock_telegram_context, mock_user):
        """Test /stats command"""
        mock_telegram_context.user_data = {"db_user": mock_user}
        
        mock_stats = {
            "total_edits": 10,
            "successful_edits": 8,
            "failed_edits": 2,
            "success_rate": 80.0,
            "recent_edits_this_month": 5,
            "favorite_edit_types": {"color_change": 3},
            "member_since": "2024-01-01",
            "last_seen": "2024-01-15",
            "recent_edits": []
        }
        
        with patch('src.bot.handlers.commands.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.commands.LoggingMiddleware.log_interaction'), \
             patch('src.bot.handlers.commands.UserService.get_user_statistics', return_value=mock_stats):
            
            await stats_command(mock_telegram_update, mock_telegram_context)
            
            # Check that reply_text was called
            mock_telegram_update.message.reply_text.assert_called_once()
            
            # Check that the message contains statistics
            call_args = mock_telegram_update.message.reply_text.call_args
            message_text = call_args[0][0]
            assert "Statistics" in message_text or "stats" in message_text.lower()
            assert "10" in message_text  # total_edits
            assert "80.0" in message_text  # success_rate


class TestMessageHandlers:
    """Test message handlers"""
    
    @pytest.mark.asyncio
    async def test_handle_photo_valid(self, mock_telegram_update, mock_telegram_context, mock_user, sample_image_bytes):
        """Test handling a valid photo"""
        # Mock photo message
        mock_photo = MagicMock()
        mock_photo.get_file = AsyncMock()
        mock_photo.get_file.return_value.download_as_bytes = AsyncMock(return_value=sample_image_bytes)
        
        mock_telegram_update.message.photo = [mock_photo]
        mock_telegram_context.user_data = {"db_user": mock_user}
        
        mock_image_info = {
            "valid": True,
            "format": "JPEG",
            "size": (1024, 1024),
            "file_size_mb": 0.5
        }
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'), \
             patch('src.bot.handlers.messages.ImageProcessor.validate_image', return_value=mock_image_info):
            
            await handle_photo(mock_telegram_update, mock_telegram_context)
            
            # Check that image was stored in context
            assert "pending_image" in mock_telegram_context.user_data
            assert mock_telegram_context.user_data["pending_image"]["bytes"] == sample_image_bytes
            
            # Check that reply was sent
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "Image Received" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_photo_invalid(self, mock_telegram_update, mock_telegram_context, mock_user):
        """Test handling an invalid photo"""
        # Mock photo message
        mock_photo = MagicMock()
        mock_photo.get_file = AsyncMock()
        mock_photo.get_file.return_value.download_as_bytes = AsyncMock(return_value=b"invalid_data")
        
        mock_telegram_update.message.photo = [mock_photo]
        mock_telegram_context.user_data = {"db_user": mock_user}
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'), \
             patch('src.bot.handlers.messages.ImageProcessor.validate_image', side_effect=Exception("Invalid image")):
            
            await handle_photo(mock_telegram_update, mock_telegram_context)
            
            # Check that error message was sent
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "Invalid Image" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_text_with_pending_image(self, mock_telegram_update, mock_telegram_context, mock_user, sample_image_bytes):
        """Test handling text with pending image"""
        mock_telegram_update.message.text = "Change the car color to red"
        mock_telegram_context.user_data = {
            "db_user": mock_user,
            "pending_image": {
                "bytes": sample_image_bytes,
                "info": {"format": "JPEG", "size": (1024, 1024)},
                "message_id": 12345
            }
        }
        
        # Mock the processing message
        mock_processing_message = MagicMock()
        mock_telegram_update.message.reply_text.return_value = mock_processing_message
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'), \
             patch('src.bot.handlers.messages.db.create_image_edit', return_value=True), \
             patch('src.bot.handlers.messages.process_image_edit') as mock_process:
            
            await handle_text(mock_telegram_update, mock_telegram_context)
            
            # Check that processing started
            mock_process.assert_called_once()
            
            # Check that processing message was sent
            mock_telegram_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_text_no_pending_image(self, mock_telegram_update, mock_telegram_context, mock_user):
        """Test handling text without pending image"""
        mock_telegram_update.message.text = "Change the car color to red"
        mock_telegram_context.user_data = {"db_user": mock_user}
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'):
            
            await handle_text(mock_telegram_update, mock_telegram_context)
            
            # Check that error message was sent
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "send an image first" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_handle_text_prompt_too_short(self, mock_telegram_update, mock_telegram_context, mock_user, sample_image_bytes):
        """Test handling text with prompt too short"""
        mock_telegram_update.message.text = "hi"
        mock_telegram_context.user_data = {
            "db_user": mock_user,
            "pending_image": {
                "bytes": sample_image_bytes,
                "info": {"format": "JPEG"},
                "message_id": 12345
            }
        }
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'):
            
            await handle_text(mock_telegram_update, mock_telegram_context)
            
            # Check that error message was sent
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "too short" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_handle_text_prompt_too_long(self, mock_telegram_update, mock_telegram_context, mock_user, sample_image_bytes):
        """Test handling text with prompt too long"""
        mock_telegram_update.message.text = "x" * 600  # Over 500 character limit
        mock_telegram_context.user_data = {
            "db_user": mock_user,
            "pending_image": {
                "bytes": sample_image_bytes,
                "info": {"format": "JPEG"},
                "message_id": 12345
            }
        }
        
        with patch('src.bot.handlers.messages.UserMiddleware.process_user', return_value=True), \
             patch('src.bot.handlers.messages.LoggingMiddleware.log_interaction'):
            
            await handle_text(mock_telegram_update, mock_telegram_context)
            
            # Check that error message was sent
            mock_telegram_update.message.reply_text.assert_called_once()
            call_args = mock_telegram_update.message.reply_text.call_args
            assert "too long" in call_args[0][0].lower()
