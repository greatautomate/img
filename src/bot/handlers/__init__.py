"""
Bot handlers for MedusaXD AI Image Editor Bot
"""

from .commands import setup_command_handlers
from .messages import setup_message_handlers
from .admin import setup_admin_handlers

__all__ = [
    "setup_command_handlers",
    "setup_message_handlers",
    "setup_admin_handlers"
]


async def setup_handlers(application, middleware):
    """Setup all bot handlers"""
    
    # Setup command handlers
    await setup_command_handlers(application, middleware)
    
    # Setup message handlers
    await setup_message_handlers(application, middleware)
    
    # Setup admin handlers
    await setup_admin_handlers(application, middleware)
    
    return True
