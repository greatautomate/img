"""
Image edit model for MongoDB storage
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId
from .user import PyObjectId


class EditStatus(str, Enum):
    """Status of image edit request"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageEdit(BaseModel):
    """Image edit request model for MongoDB"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # User information
    user_id: PyObjectId
    telegram_user_id: int
    telegram_message_id: int
    
    # Edit request details
    prompt: str
    original_image_url: Optional[str] = None
    original_image_size: Optional[int] = None  # Size in bytes
    
    # BFL.ai API details
    bfl_request_id: Optional[str] = None
    bfl_polling_url: Optional[str] = None
    
    # Edit parameters
    aspect_ratio: str = "1:1"
    output_format: str = "jpeg"
    seed: Optional[int] = None
    safety_tolerance: int = 2
    
    # Results
    edited_image_url: Optional[str] = None
    edited_image_downloaded: bool = False
    local_image_path: Optional[str] = None
    
    # Status and timing
    status: EditStatus = EditStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Metadata
    edit_type: Optional[str] = None  # e.g., "color_change", "text_edit", "object_removal"
    tags: list[str] = Field(default_factory=list)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "telegram_user_id": 123456789,
                "telegram_message_id": 12345,
                "prompt": "Change the car color to red",
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "status": "pending",
                "edit_type": "color_change",
                "tags": ["car", "color", "red"]
            }
        }
    
    def start_processing(self, bfl_request_id: str, bfl_polling_url: str):
        """Mark edit as started processing"""
        self.status = EditStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.bfl_request_id = bfl_request_id
        self.bfl_polling_url = bfl_polling_url
    
    def complete_successfully(self, edited_image_url: str):
        """Mark edit as completed successfully"""
        self.status = EditStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.edited_image_url = edited_image_url
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
    
    def fail_with_error(self, error_message: str):
        """Mark edit as failed with error"""
        self.status = EditStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
    
    def can_retry(self) -> bool:
        """Check if edit can be retried"""
        return self.retry_count < self.max_retries and self.status == EditStatus.FAILED
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.status = EditStatus.PENDING
        self.error_message = None
    
    def cancel(self):
        """Cancel the edit request"""
        self.status = EditStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if edit is completed (success or failure)"""
        return self.status in [EditStatus.COMPLETED, EditStatus.FAILED, EditStatus.CANCELLED]
    
    @property
    def is_successful(self) -> bool:
        """Check if edit was successful"""
        return self.status == EditStatus.COMPLETED
    
    def classify_edit_type(self) -> str:
        """Classify the edit type based on prompt"""
        prompt_lower = self.prompt.lower()
        
        # Text editing
        if any(word in prompt_lower for word in ["replace", "text", "word", "letter", "font"]):
            return "text_edit"
        
        # Color changes
        if any(word in prompt_lower for word in ["color", "colour", "red", "blue", "green", "yellow", "purple", "orange", "pink", "black", "white"]):
            return "color_change"
        
        # Object removal/addition
        if any(word in prompt_lower for word in ["remove", "delete", "add", "insert", "place"]):
            return "object_modification"
        
        # Background changes
        if any(word in prompt_lower for word in ["background", "sky", "scene", "setting"]):
            return "background_change"
        
        # Style changes
        if any(word in prompt_lower for word in ["style", "artistic", "painting", "sketch", "cartoon"]):
            return "style_change"
        
        return "general_edit"
