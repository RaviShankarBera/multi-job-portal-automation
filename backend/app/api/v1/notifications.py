from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.notification import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    BulkNotificationResponse
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="Filter by unread notifications only"),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List notifications for the current user."""
    notification_service = NotificationService(db)
    
    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    
    # Get total count
    all_notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=False
    )
    total = len(all_notifications)
    
    # Get unread count
    unread_count = await notification_service.get_unread_count(current_user.id)
    
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications for the current user."""
    notification_service = NotificationService(db)
    unread_count = await notification_service.get_unread_count(current_user.id)
    return UnreadCountResponse(unread_count=unread_count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read."""
    notification_service = NotificationService(db)
    
    notification = await notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    return NotificationResponse.model_validate(notification)


@router.put("/read-all", response_model=BulkNotificationResponse)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read for the current user."""
    notification_service = NotificationService(db)
    
    count = await notification_service.mark_all_as_read(current_user.id)
    
    return BulkNotificationResponse(
        message=f"Successfully marked {count} notifications as read",
        count=count
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification."""
    notification_service = NotificationService(db)
    
    success = await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete notification")
    
    return {"message": "Notification deleted successfully"}
