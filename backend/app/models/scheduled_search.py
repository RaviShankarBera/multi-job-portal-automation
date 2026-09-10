from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from app.core.database import Base


class SearchFrequency(str, Enum):
    """Search frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ScheduledSearch(Base):
    """Scheduled search model for automated job searches."""
    
    __tablename__ = "scheduled_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    search_params = Column(JSON, nullable=False)
    min_match_score = Column(Float, default=80.0, nullable=False)
    frequency = Column(String(20), nullable=False, default="daily")
    time_of_day = Column(String(5), nullable=True, default="08:00")
    is_active = Column(Boolean, default=True, nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_searches")
    
    def __repr__(self) -> str:
        return f"<ScheduledSearch(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    def calculate_next_run(self) -> None:
        """Calculate next run time based on frequency and time_of_day."""
        from datetime import timedelta
        
        now = datetime.utcnow()
        hour, minute = map(int, self.time_of_day.split(":")) if self.time_of_day else (8, 0)
        
        if self.frequency == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            self.next_run = next_run
        elif self.frequency == "weekly":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = 7 - now.weekday()  # Assuming Monday
            if days_ahead <= 0:
                days_ahead += 7
            next_run += timedelta(days=days_ahead)
            self.next_run = next_run
        elif self.frequency == "custom":
            # For custom, we'll just schedule for the next day at the specified time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            self.next_run = next_run
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduled search to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "search_params": self.search_params,
            "min_match_score": self.min_match_score,
            "frequency": self.frequency,
            "time_of_day": self.time_of_day,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
