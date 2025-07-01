"""
User model for MongoDB storage
"""

from datetime import datetime
from typing import Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator, BeforeValidator
from bson import ObjectId


def validate_object_id(v):
    """Validator function for ObjectId - Pydantic v2 compatible"""
    if v is None:
        return ObjectId()
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId string")
    raise ValueError(f"Invalid ObjectId type: {type(v)}")


# Use Annotated with BeforeValidator for Pydantic v2
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class UserStats(BaseModel):
    """User statistics model"""
    
    model_config = ConfigDict(
        json_encoders={ObjectId: str}
    )
    
    total_edits: int = 0
    successful_edits: int = 0
    failed_edits: int = 0
    total_images_processed: int = 0
    favorite_edit_types: Dict[str, int] = Field(default_factory=dict)
    last_edit_date: Optional[datetime] = None


class User(BaseModel):
    """User model for MongoDB"""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
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
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    telegram_user_id: int = Field(..., description="Unique Telegram user ID")
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
    
    @field_validator('telegram_user_id')
    @classmethod
    def validate_telegram_user_id(cls, v):
        if v <= 0:
            raise ValueError('telegram_user_id must be positive')
        return v
    
    @field_validator('preferred_aspect_ratio')
    @classmethod
    def validate_aspect_ratio(cls, v):
        valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]
        if v not in valid_ratios:
            raise ValueError(f'aspect_ratio must be one of {valid_ratios}')
        return v
    
    @field_validator('preferred_output_format')
    @classmethod
    def validate_output_format(cls, v):
        valid_formats = ["jpeg", "png", "webp"]
        if v.lower() not in valid_formats:
            raise ValueError(f'output_format must be one of {valid_formats}')
        return v.lower()
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB insertion"""
        data = self.model_dump(by_alias=True)
        # Ensure ObjectId is properly handled
        if '_id' not in data or data['_id'] is None:
            data['_id'] = ObjectId()
        elif isinstance(data['_id'], str):
            data['_id'] = ObjectId(data['_id'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from dictionary"""
        return cls(**data)
    
    def model_dump_for_mongo(self) -> Dict[str, Any]:
        """Dump model data specifically formatted for MongoDB"""
        data = self.model_dump(by_alias=True, exclude_unset=True)
        
        # Handle ObjectId conversion
        if '_id' in data and data['_id'] is not None:
            if isinstance(data['_id'], str):
                data['_id'] = ObjectId(data['_id'])
        elif '_id' not in data:
            data['_id'] = ObjectId()
            
        return data
