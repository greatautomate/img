"""
User model for MongoDB storage
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserStats(BaseModel):
    """User statistics model"""
    total_edits: int = 0
    successful_edits: int = 0
    failed_edits: int = 0
    total_images_processed: int = 0
    favorite_edit_types: Dict[str, int] = Field(default_factory=dict)
    last_edit_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}


class User(BaseModel):
    """User model for MongoDB"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    telegram_user_id: int = Field(..., unique=True)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = "en"
    
    # User preferences
    preferred_aspect_ratio: str = "1:1"
    preferred_output_format: str = "jpeg"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    stats: UserStats = Field(default_factory=UserStats)
    
    # User state
    is_active: bool = True
    is_premium: bool = False
    is_banned: bool = False
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "telegram_user_id": 123456789,
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe",
                "language_code": "en",
                "preferred_aspect_ratio": "1:1",
                "preferred_output_format": "jpeg",
                "is_active": True,
                "is_premium": False,
                "is_banned": False
            }
        }
    
    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_edit_count(self, success: bool = True):
        """Increment edit statistics"""
        self.stats.total_edits += 1
        if success:
            self.stats.successful_edits += 1
        else:
            self.stats.failed_edits += 1
        self.stats.last_edit_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_favorite_edit_type(self, edit_type: str):
        """Add or increment favorite edit type"""
        if edit_type in self.stats.favorite_edit_types:
            self.stats.favorite_edit_types[edit_type] += 1
        else:
            self.stats.favorite_edit_types[edit_type] = 1
        self.updated_at = datetime.utcnow()
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_user_id}"
    
    @property
    def success_rate(self) -> float:
        """Calculate edit success rate"""
        if self.stats.total_edits == 0:
            return 0.0
        return (self.stats.successful_edits / self.stats.total_edits) * 100
