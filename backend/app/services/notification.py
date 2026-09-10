from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select

from app.models.notification import Notification, NotificationType
from app.core.exceptions import NotFoundError, ValidationError


class NotificationService:
    """Service for managing user notifications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_notification(
        self,
        user_id: int,
        type: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ) -> Notification:
        """Create a new notification for a user.
        
        Args:
            user_id: ID of the user to notify.
            type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Optional additional data.
            
        Returns:
            Created notification.
        """
        # Validate notification type
        try:
            NotificationType(type)
        except ValueError:
            raise ValidationError(f"Invalid notification type: {type}")
        
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data
        )
        
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        
        return notification
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user.
        
        Args:
            user_id: ID of the user.
            unread_only: If True, only return unread notifications.
            skip: Number of notifications to skip.
            limit: Maximum number of notifications to return.
            
        Returns:
            List of notifications.
        """
        query = select(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_notification_by_id(self, notification_id: int, user_id: int) -> Notification:
        """Get a notification by ID for a specific user.
        
        Args:
            notification_id: ID of the notification.
            user_id: ID of the user who owns the notification.
            
        Returns:
            The notification.
            
        Raises:
            NotFoundError: If notification not found.
        """
        query = select(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise NotFoundError("Notification", notification_id)
        
        return notification
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """Mark a notification as read.
        
        Args:
            notification_id: ID of the notification.
            user_id: ID of the user who owns the notification.
            
        Returns:
            Updated notification.
        """
        notification = await self.get_notification_by_id(notification_id, user_id)
        
        if not notification.is_read:
            notification.mark_as_read()
            await self.db.flush()
            await self.db.refresh(notification)
        
        return notification
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            Number of notifications marked as read.
        """
        query = select(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())
        
        count = 0
        for notification in notifications:
            notification.mark_as_read()
            count += 1
        
        await self.db.flush()
        
        return count
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            Number of unread notifications.
        """
        query = select(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification.
        
        Args:
            notification_id: ID of the notification.
            user_id: ID of the user who owns the notification.
            
        Returns:
            True if deleted, False otherwise.
        """
        notification = await self.get_notification_by_id(notification_id, user_id)
        
        await self.db.delete(notification)
        await self.db.flush()
        
        return True
    
    async def delete_all_notifications(self, user_id: int) -> int:
        """Delete all notifications for a user.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            Number of notifications deleted.
        """
        query = select(Notification).filter(
            Notification.user_id == user_id
        )
        
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())
        
        count = len(notifications)
        for notification in notifications:
            await self.db.delete(notification)
        
        await self.db.flush()
        
        return count
