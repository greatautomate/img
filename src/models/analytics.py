"""
Analytics model for MongoDB storage
"""

from datetime import datetime, date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from .user import PyObjectId


class DailyStats(BaseModel):
    """Daily statistics model"""
    date: date
    total_users: int = 0
    new_users: int = 0
    active_users: int = 0
    total_edits: int = 0
    successful_edits: int = 0
    failed_edits: int = 0
    average_processing_time: Optional[float] = None
    popular_edit_types: Dict[str, int] = Field(default_factory=dict)


class BotAnalytics(BaseModel):
    """Bot analytics model for MongoDB"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Overall statistics
    total_users: int = 0
    total_edits: int = 0
    successful_edits: int = 0
    failed_edits: int = 0
    
    # Performance metrics
    average_processing_time: Optional[float] = None
    success_rate: float = 0.0
    
    # Popular features
    popular_edit_types: Dict[str, int] = Field(default_factory=dict)
    popular_aspect_ratios: Dict[str, int] = Field(default_factory=dict)
    popular_output_formats: Dict[str, int] = Field(default_factory=dict)
    
    # Daily statistics
    daily_stats: List[DailyStats] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str}
    
    def update_stats(self, 
                    new_user: bool = False,
                    edit_success: bool = True,
                    processing_time: Optional[float] = None,
                    edit_type: Optional[str] = None,
                    aspect_ratio: Optional[str] = None,
                    output_format: Optional[str] = None):
        """Update analytics with new data"""
        
        # Update overall stats
        if new_user:
            self.total_users += 1
        
        self.total_edits += 1
        if edit_success:
            self.successful_edits += 1
        else:
            self.failed_edits += 1
        
        # Update success rate
        self.success_rate = (self.successful_edits / self.total_edits) * 100
        
        # Update average processing time
        if processing_time:
            if self.average_processing_time:
                # Calculate running average
                total_time = self.average_processing_time * (self.total_edits - 1)
                self.average_processing_time = (total_time + processing_time) / self.total_edits
            else:
                self.average_processing_time = processing_time
        
        # Update popular features
        if edit_type:
            self.popular_edit_types[edit_type] = self.popular_edit_types.get(edit_type, 0) + 1
        
        if aspect_ratio:
            self.popular_aspect_ratios[aspect_ratio] = self.popular_aspect_ratios.get(aspect_ratio, 0) + 1
        
        if output_format:
            self.popular_output_formats[output_format] = self.popular_output_formats.get(output_format, 0) + 1
        
        # Update daily stats
        today = date.today()
        daily_stat = next((stat for stat in self.daily_stats if stat.date == today), None)
        
        if not daily_stat:
            daily_stat = DailyStats(date=today)
            self.daily_stats.append(daily_stat)
        
        if new_user:
            daily_stat.new_users += 1
        
        daily_stat.total_edits += 1
        if edit_success:
            daily_stat.successful_edits += 1
        else:
            daily_stat.failed_edits += 1
        
        if processing_time:
            if daily_stat.average_processing_time:
                total_time = daily_stat.average_processing_time * (daily_stat.total_edits - 1)
                daily_stat.average_processing_time = (total_time + processing_time) / daily_stat.total_edits
            else:
                daily_stat.average_processing_time = processing_time
        
        if edit_type:
            daily_stat.popular_edit_types[edit_type] = daily_stat.popular_edit_types.get(edit_type, 0) + 1
        
        self.updated_at = datetime.utcnow()
    
    def get_daily_stats(self, days: int = 7) -> List[DailyStats]:
        """Get daily stats for the last N days"""
        cutoff_date = date.today() - datetime.timedelta(days=days)
        return [stat for stat in self.daily_stats if stat.date >= cutoff_date]
    
    def get_top_edit_types(self, limit: int = 5) -> List[tuple]:
        """Get top edit types by popularity"""
        return sorted(self.popular_edit_types.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        return {
            "total_users": self.total_users,
            "total_edits": self.total_edits,
            "success_rate": round(self.success_rate, 2),
            "average_processing_time": round(self.average_processing_time or 0, 2),
            "top_edit_types": self.get_top_edit_types(),
            "last_updated": self.updated_at
        }
