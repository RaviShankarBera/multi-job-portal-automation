import time
import logging
from datetime import datetime
from typing import Dict, Any

from celery_app import celery_app
from app.core.database import async_session_factory
from app.services.scheduled_search import ScheduledSearchService
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.scheduled_searches.execute_due_searches",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def execute_due_searches(self) -> Dict[str, Any]:
    """Execute all scheduled searches that are due to run.
    
    This task is called by Celery Beat every 15 minutes.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                scheduled_search_service = ScheduledSearchService(db)
                
                # Get all due searches
                due_searches = await scheduled_search_service.get_due_searches()
                
                results = []
                for search in due_searches:
                    try:
                        result = execute_scheduled_search.delay(search.id)
                        results.append({
                            "search_id": search.id,
                            "task_id": result.id,
                            "status": "queued"
                        })
                        logger.info(f"Queued search {search.id} for execution")
                    except Exception as e:
                        logger.error(f"Failed to queue search {search.id}: {str(e)}")
                        results.append({
                            "search_id": search.id,
                            "task_id": None,
                            "status": "failed",
                            "error": str(e)
                        })
                
                execution_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "searches_queued": len([r for r in results if r["status"] == "queued"]),
                    "searches_failed": len([r for r in results if r["status"] == "failed"]),
                    "execution_time": execution_time,
                    "details": results
                }
            
            except Exception as e:
                logger.error(f"Error in execute_due_searches: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error in execute_due_searches: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.scheduled_searches.execute_scheduled_search",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def execute_scheduled_search(self, search_id: int) -> Dict[str, Any]:
    """Execute a specific scheduled search.
    
    Args:
        search_id: ID of the scheduled search to execute.
        
    Returns:
        Execution results.
    """
    import asyncio
    
    start_time = time.time()
    
    async def _execute():
        async with async_session_factory() as db:
            try:
                scheduled_search_service = ScheduledSearchService(db)
                
                # Execute the search
                result = await scheduled_search_service.execute_scheduled_search(search_id)
                
                execution_time = time.time() - start_time
                logger.info(
                    f"Executed search {search_id}: "
                    f"Found {result['jobs_found']} jobs, "
                    f"{result['high_match_count']} high-match"
                )
                
                return {
                    "status": "success",
                    "search_id": search_id,
                    "jobs_found": result["jobs_found"],
                    "high_match_count": result["high_match_count"],
                    "execution_time": execution_time
                }
            
            except Exception as e:
                logger.error(f"Error executing search {search_id}: {str(e)}")
                raise
            
            finally:
                await db.close()
    
    try:
        return asyncio.run(_execute())
    except Exception as e:
        logger.error(f"Error executing search {search_id}: {str(e)}")
        raise self.retry(exc=e)
