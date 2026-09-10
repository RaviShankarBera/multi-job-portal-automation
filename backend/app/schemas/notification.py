from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enumeration."""
    NEW_JOB = "new_job"
    APPLICATION_UPDATE = "application_update"
    FOLLOW_UP = "follow_up"
    INTERVIEW = "interview"
    DEADLINE = "deadline"
    SYSTEM = "system"


class NotificationCreate(BaseModel):
    """Schema for creating notifications."""
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Schema for notification responses."""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for notification list responses."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int


class UnreadCountResponse(BaseModel):
    """Schema for unread count responses."""
    unread_count: int


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""
    is_read: Optional[bool] = None


class BulkNotificationResponse(BaseModel):
    """Schema for bulk notification operations."""
    message: str
    count: int
