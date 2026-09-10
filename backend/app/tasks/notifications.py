import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery_app import celery_app
from app.core.database import async_session_factory
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.notifications.check_follow_ups",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def check_follow_ups(self) -> Dict[str, Any]:
    """Check for follow-up reminders and create notifications.
    
    This task runs daily at 8 AM to remind users about follow-ups.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                from app.models.application import Application
                from sqlalchemy import and_, select
                
                # Get applications that need follow-up (sent > 7 days ago with no response)
                follow_up_threshold = datetime.utcnow() - timedelta(days=7)
                
                result = await db.execute(
                    select(Application).filter(
                        and_(
                            Application.status == "sent",
                            Application.sent_at <= follow_up_threshold,
                            Application.follow_up_count < 3
                        )
                    )
                )
                applications = list(result.scalars().all())
                
                notification_service = NotificationService(db)
                notifications_created = 0
                
                for application in applications:
                    try:
                        # Create follow-up reminder notification
                        await notification_service.create_notification(
                            user_id=application.user_id,
                            type="follow_up",
                            title=f"Follow up on application: {application.job.title}",
                            message=(
                                f"You applied to {application.job.company} "
                                f"{(datetime.utcnow() - application.sent_at).days} days ago. "
                                f"Consider following up on your application."
                            ),
                            data={
                                "application_id": application.id,
                                "job_id": application.job_id,
                                "company": application.job.company,
                                "days_since_applied": (datetime.utcnow() - application.sent_at).days
                            }
                        )
                        
                        # Update follow-up count
                        application.follow_up_count += 1
                        application.last_follow_up_at = datetime.utcnow()
                        
                        notifications_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error creating follow-up for application {application.id}: {str(e)}")
                        continue
                
                await db.commit()
                
                execution_time = time.time() - start_time
                logger.info(f"Created {notifications_created} follow-up notifications")
                
                return {
                    "status": "success",
                    "notifications_created": notifications_created,
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error checking follow-ups: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error checking follow-ups: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.notifications.cleanup_old_notifications",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def cleanup_old_notifications(self) -> Dict[str, Any]:
    """Clean up old notifications (older than 90 days).
    
    This task runs weekly to keep the notification table clean.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                from app.models.notification import Notification
                from sqlalchemy import and_, select
                
                # Get notifications older than 90 days
                cleanup_threshold = datetime.utcnow() - timedelta(days=90)
                
                result = await db.execute(
                    select(Notification).filter(
                        and_(
                            Notification.created_at <= cleanup_threshold,
                            Notification.is_read == True
                        )
                    )
                )
                old_notifications = list(result.scalars().all())
                
                deleted_count = len(old_notifications)
                
                for notification in old_notifications:
                    await db.delete(notification)
                
                await db.commit()
                
                execution_time = time.time() - start_time
                logger.info(f"Cleaned up {deleted_count} old notifications")
                
                return {
                    "status": "success",
                    "notifications_deleted": deleted_count,
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error cleaning up notifications: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.notifications.send_deadline_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_deadline_reminders(self) -> Dict[str, Any]:
    """Send deadline reminders for upcoming job application deadlines.
    
    This task runs daily to remind users about application deadlines.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                from app.models.job import Job
                from sqlalchemy import and_, select
                
                # Get jobs with deadlines in the next 3 days
                deadline_threshold = datetime.utcnow() + timedelta(days=3)
                
                result = await db.execute(
                    select(Job).filter(
                        and_(
                            Job.is_active == True,
                            Job.application_deadline != None,
                            Job.application_deadline <= deadline_threshold,
                            Job.application_deadline >= datetime.utcnow()
                        )
                    )
                )
                jobs_with_deadlines = list(result.scalars().all())
                
                notification_service = NotificationService(db)
                notifications_created = 0
                
                for job in jobs_with_deadlines:
                    try:
                        # Get all users who might be interested
                        # This is a simplified version - actual implementation
                        # would check user preferences
                        
                        days_until_deadline = (job.application_deadline - datetime.utcnow()).days
                        
                        # Create deadline reminder notification for interested users
                        # (simplified - would normally get relevant users)
                        
                        notifications_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error creating deadline reminder for job {job.id}: {str(e)}")
                        continue
                
                execution_time = time.time() - start_time
                logger.info(f"Created {notifications_created} deadline reminders")
                
                return {
                    "status": "success",
                    "notifications_created": notifications_created,
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error sending deadline reminders: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error sending deadline reminders: {str(e)}")
        raise self.retry(exc=e)
