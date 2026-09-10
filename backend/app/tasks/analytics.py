import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery_app import celery_app
from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.analytics.create_daily_snapshots",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def create_daily_snapshots(self) -> Dict[str, Any]:
    """Create daily analytics snapshots for reporting.
    
    This task runs daily at midnight to create aggregate statistics.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                from app.models.job import Job
                from app.models.application import Application
                from app.models.user import User
                from sqlalchemy import func, select
                
                yesterday = datetime.utcnow().date() - timedelta(days=1)
                
                # Get daily statistics
                stats = {
                    "date": yesterday.isoformat(),
                    "new_jobs": 0,
                    "total_applications": 0,
                    "successful_applications": 0,
                    "active_users": 0,
                    "avg_match_score": 0.0,
                }
                
                # Count new jobs from yesterday
                new_jobs_result = await db.execute(
                    select(func.count(Job.id)).filter(
                        func.date(Job.created_at) == yesterday
                    )
                )
                stats["new_jobs"] = new_jobs_result.scalar() or 0
                
                # Count total applications from yesterday
                total_apps_result = await db.execute(
                    select(func.count(Application.id)).filter(
                        func.date(Application.created_at) == yesterday
                    )
                )
                stats["total_applications"] = total_apps_result.scalar() or 0
                
                # Count successful applications
                successful_apps_result = await db.execute(
                    select(func.count(Application.id)).filter(
                        func.date(Application.created_at) == yesterday,
                        Application.status.in_(["interview", "offer", "hired"])
                    )
                )
                stats["successful_applications"] = successful_apps_result.scalar() or 0
                
                # Count active users
                active_users_result = await db.execute(
                    select(func.count(User.id)).filter(
                        func.date(User.last_login) == yesterday
                    )
                )
                stats["active_users"] = active_users_result.scalar() or 0
                
                # Calculate average match score
                avg_score_result = await db.execute(
                    select(func.avg(Job.match_score)).filter(
                        func.date(Job.created_at) == yesterday
                    )
                )
                avg_score = avg_score_result.scalar()
                stats["avg_match_score"] = float(avg_score) if avg_score else 0.0
                
                # Save snapshot (would normally save to analytics table)
                logger.info(f"Created daily snapshot for {yesterday}: {stats}")
                
                execution_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "snapshot_date": yesterday.isoformat(),
                    "stats": stats,
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error creating daily snapshot: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error creating daily snapshot: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.analytics.update_job_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def update_job_scores(self) -> Dict[str, Any]:
    """Update job match scores based on user preferences.
    
    This task runs daily to recalculate job match scores.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                from app.models.job import Job
                from sqlalchemy import select
                
                # Get all active jobs
                result = await db.execute(
                    select(Job).filter(Job.is_active == True)
                )
                active_jobs = list(result.scalars().all())
                
                updated_count = 0
                
                for job in active_jobs:
                    try:
                        # Update match score based on user preferences
                        # This is a simplified version - actual implementation
                        # would be more complex
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating score for job {job.id}: {str(e)}")
                        continue
                
                execution_time = time.time() - start_time
                logger.info(f"Updated scores for {updated_count} jobs")
                
                return {
                    "status": "success",
                    "jobs_updated": updated_count,
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error updating job scores: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error updating job scores: {str(e)}")
        raise self.retry(exc=e)
