from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SearchFrequency(str, Enum):
    """Search frequency enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ScheduledSearchCreate(BaseModel):
    """Schema for creating scheduled searches."""
    name: str = Field(..., min_length=1, max_length=255)
    search_params: Dict[str, Any]
    min_match_score: float = Field(default=80.0, ge=0, le=100)
    frequency: SearchFrequency = SearchFrequency.DAILY
    time_of_day: Optional[str] = Field(default="08:00", pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_active: bool = True


class ScheduledSearchUpdate(BaseModel):
    """Schema for updating scheduled searches."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    search_params: Optional[Dict[str, Any]] = None
    min_match_score: Optional[float] = Field(None, ge=0, le=100)
    frequency: Optional[SearchFrequency] = None
    time_of_day: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_active: Optional[bool] = None


class ScheduledSearchResponse(BaseModel):
    """Schema for scheduled search responses."""
    id: int
    user_id: int
    name: str
    search_params: Dict[str, Any]
    min_match_score: float
    frequency: str
    time_of_day: Optional[str] = None
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScheduledSearchListResponse(BaseModel):
    """Schema for scheduled search list responses."""
    scheduled_searches: List[ScheduledSearchResponse]
    total: int


class ScheduledSearchExecutionResponse(BaseModel):
    """Schema for scheduled search execution responses."""
    search_id: int
    jobs_found: int
    high_match_count: int
    message: str
    execution_time: float
