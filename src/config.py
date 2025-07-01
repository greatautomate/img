"""
Configuration management for MedusaXD AI Image Editor Bot
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field



class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Telegram Bot Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    bot_username: str = Field("MedusaXDAIBot", env="BOT_USERNAME")
    
    # BFL.ai API Configuration
    bfl_api_key: str = Field(..., env="BFL_API_KEY")
    bfl_api_base_url: str = Field("https://api.bfl.ai/v1", env="BFL_API_BASE_URL")
    
    # Database Configuration
    mongodb_url: str = Field(..., env="MONGODB_URL")
    database_name: str = Field("medusaxd_bot", env="DATABASE_NAME")
    
    # Application Configuration
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_image_size_mb: int = Field(20, env="MAX_IMAGE_SIZE_MB")
    polling_interval_seconds: int = Field(2, env="POLLING_INTERVAL_SECONDS")
    max_polling_attempts: int = Field(150, env="MAX_POLLING_ATTEMPTS")
    
    # Optional: Webhook Configuration
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    
    # Optional: Redis Configuration
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # Security
    admin_user_ids: List[int] = Field(default_factory=list, env="ADMIN_USER_IDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse admin user IDs from comma-separated string
        if isinstance(self.admin_user_ids, str):
            self.admin_user_ids = [
                int(uid.strip()) for uid in self.admin_user_ids.split(",") 
                if uid.strip().isdigit()
            ]


# Global settings instance
settings = Settings()


# Bot branding constants
BOT_NAME = "MedusaXD AI Image Editor"
BOT_DESCRIPTION = "🎨 Transform your images with AI-powered editing using FLUX.1 Kontext [pro]"
BOT_VERSION = "1.0.0"

# API endpoints
BFL_ENDPOINTS = {
    "kontext_pro": "/flux-kontext-pro",
    "get_result": "/get_result"
}

# Image processing constants
SUPPORTED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP"]
MAX_IMAGE_PIXELS = 20_000_000  # 20 megapixels
DEFAULT_ASPECT_RATIO = "1:1"

# Response messages
MESSAGES = {
    "welcome": f"""
🎨 **Welcome to {BOT_NAME}!**

I'm your AI-powered image editing assistant. Send me an image and tell me how you'd like to edit it!

**What I can do:**
• 🎯 **Simple Editing**: Change specific parts while keeping the rest untouched
• 🧠 **Smart Changes**: Make natural edits that blend seamlessly
• 📝 **Text Editing**: Add or modify text within images

**How to use:**
1. Send me an image (up to 20MB)
2. Tell me what you want to edit
3. Wait for the magic! ✨

Type /help for more information.
    """,
    
    "help": f"""
🔧 **{BOT_NAME} Help**

**Commands:**
• `/start` - Start the bot
• `/help` - Show this help message
• `/stats` - View your usage statistics
• `/about` - About this bot

**How to edit images:**
1. **Send an image** - Upload any image (JPEG, PNG, WEBP)
2. **Describe your edit** - Tell me what you want to change

**Example prompts:**
• "Change the car color to red"
• "Replace 'Hello' with 'Welcome'"
• "Add a sunset background"
• "Remove the person from the image"
• "Make the sky more dramatic"

**Tips:**
• Be specific in your descriptions
• For text editing, use quotes: Replace 'old text' with 'new text'
• Images are processed at 1024x1024 resolution
• Processing takes 30-60 seconds

Need help? Contact support!
    """,
    
    "about": f"""
ℹ️ **About {BOT_NAME}**

**Version:** {BOT_VERSION}
**Powered by:** BFL.ai FLUX.1 Kontext [pro]
**Developer:** MedusaXD Team

This bot uses state-of-the-art AI technology from Black Forest Labs to provide professional-quality image editing through simple text commands.

**Technology:**
• FLUX.1 Kontext [pro] model
• Advanced neural networks
• Real-time image processing

**Privacy:**
• Images are processed securely
• No permanent storage of your images
• Your privacy is our priority

Visit our website for more information!
    """
}
