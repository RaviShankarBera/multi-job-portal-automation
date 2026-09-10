import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

from app.models.scheduled_search import ScheduledSearch, SearchFrequency
from app.core.exceptions import NotFoundError, ValidationError


class ScheduledSearchService:
    """Service for managing scheduled job searches."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_scheduled_search(
        self,
        user_id: int,
        data: Dict[str, Any]
    ) -> ScheduledSearch:
        """Create a new scheduled search.
        
        Args:
            user_id: ID of the user.
            data: Search configuration data.
            
        Returns:
            Created scheduled search.
        """
        # Validate frequency
        frequency = data.get("frequency", "daily")
        try:
            SearchFrequency(frequency)
        except ValueError:
            raise ValidationError(f"Invalid frequency: {frequency}")
        
        # Validate time format
        time_of_day = data.get("time_of_day", "08:00")
        if not self._validate_time_format(time_of_day):
            raise ValidationError(f"Invalid time format: {time_of_day}. Use HH:MM format.")
        
        # Validate search_params
        search_params = data.get("search_params")
        if not search_params:
            raise ValidationError("search_params is required")
        
        scheduled_search = ScheduledSearch(
            user_id=user_id,
            name=data["name"],
            search_params=search_params,
            min_match_score=data.get("min_match_score", 80.0),
            frequency=frequency,
            time_of_day=time_of_day,
            is_active=data.get("is_active", True)
        )
        
        # Calculate next run time
        scheduled_search.calculate_next_run()
        
        self.db.add(scheduled_search)
        await self.db.flush()
        await self.db.refresh(scheduled_search)
        
        return scheduled_search
    
    async def get_user_scheduled_searches(
        self,
        user_id: int,
        include_inactive: bool = False
    ) -> List[ScheduledSearch]:
        """Get all scheduled searches for a user.
        
        Args:
            user_id: ID of the user.
            include_inactive: If True, include inactive searches.
            
        Returns:
            List of scheduled searches.
        """
        query = select(ScheduledSearch).filter(
            ScheduledSearch.user_id == user_id
        )
        
        if not include_inactive:
            query = query.filter(ScheduledSearch.is_active == True)
        
        query = query.order_by(ScheduledSearch.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_scheduled_search_by_id(
        self,
        search_id: int,
        user_id: int
    ) -> ScheduledSearch:
        """Get a scheduled search by ID for a specific user.
        
        Args:
            search_id: ID of the scheduled search.
            user_id: ID of the user who owns the search.
            
        Returns:
            The scheduled search.
            
        Raises:
            NotFoundError: If scheduled search not found.
        """
        query = select(ScheduledSearch).filter(
            and_(
                ScheduledSearch.id == search_id,
                ScheduledSearch.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        scheduled_search = result.scalar_one_or_none()
        
        if not scheduled_search:
            raise NotFoundError("Scheduled search", search_id)
        
        return scheduled_search
    
    async def update_scheduled_search(
        self,
        search_id: int,
        user_id: int,
        data: Dict[str, Any]
    ) -> ScheduledSearch:
        """Update a scheduled search.
        
        Args:
            search_id: ID of the scheduled search.
            user_id: ID of the user who owns the search.
            data: Updated search configuration data.
            
        Returns:
            Updated scheduled search.
        """
        scheduled_search = await self.get_scheduled_search_by_id(search_id, user_id)
        
        # Update fields if provided
        if "name" in data:
            scheduled_search.name = data["name"]
        if "search_params" in data:
            scheduled_search.search_params = data["search_params"]
        if "min_match_score" in data:
            scheduled_search.min_match_score = data["min_match_score"]
        if "frequency" in data:
            frequency = data["frequency"]
            try:
                SearchFrequency(frequency)
            except ValueError:
                raise ValidationError(f"Invalid frequency: {frequency}")
            scheduled_search.frequency = frequency
        if "time_of_day" in data:
            time_of_day = data["time_of_day"]
            if not self._validate_time_format(time_of_day):
                raise ValidationError(f"Invalid time format: {time_of_day}. Use HH:MM format.")
            scheduled_search.time_of_day = time_of_day
        if "is_active" in data:
            scheduled_search.is_active = data["is_active"]
        
        # Recalculate next run if frequency or time changed
        if "frequency" in data or "time_of_day" in data:
            scheduled_search.calculate_next_run()
        
        await self.db.flush()
        await self.db.refresh(scheduled_search)
        
        return scheduled_search
    
    async def delete_scheduled_search(self, search_id: int, user_id: int) -> bool:
        """Delete a scheduled search.
        
        Args:
            search_id: ID of the scheduled search.
            user_id: ID of the user who owns the search.
            
        Returns:
            True if deleted, False otherwise.
        """
        scheduled_search = await self.get_scheduled_search_by_id(search_id, user_id)
        
        await self.db.delete(scheduled_search)
        await self.db.flush()
        
        return True
    
    async def execute_scheduled_search(self, search_id: int) -> Dict[str, Any]:
        """Execute a scheduled search.
        
        Args:
            search_id: ID of the scheduled search.
            
        Returns:
            Execution results.
        """
        from app.services.job import JobService
        from app.services.notification import NotificationService
        from app.schemas.job import JobSearchParams
        
        query = select(ScheduledSearch).filter(ScheduledSearch.id == search_id)
        result = await self.db.execute(query)
        scheduled_search = result.scalar_one_or_none()
        
        if not scheduled_search:
            raise NotFoundError("Scheduled search", search_id)
        
        start_time = time.time()
        
        # Execute the search using JobService
        job_service = JobService(self.db)
        search_params = scheduled_search.search_params
        
        # Create JobSearchParams from stored data
        job_params = JobSearchParams(
            keywords=search_params.get("query", ""),
            location=search_params.get("location"),
            remote=search_params.get("remote_only", False),
            experience_min=search_params.get("experience_min"),
            experience_max=search_params.get("experience_max"),
            salary_min=search_params.get("salary_min"),
            salary_max=search_params.get("salary_max"),
            company=search_params.get("company"),
            employment_type=search_params.get("job_type"),
            page=1,
            page_size=50
        )
        
        # Run the search
        jobs, total = await job_service.search_jobs(
            user_id=scheduled_search.user_id,
            params=job_params
        )
        
        # Deduplicate jobs
        unique_jobs = await job_service.deduplicate_jobs(jobs)
        
        # Score and filter by match score
        high_match_jobs = [
            job for job in unique_jobs
            if hasattr(job, 'match_score') and (job.match_score or 0) >= scheduled_search.min_match_score
        ]
        
        # Notify user of high-match jobs
        if high_match_jobs:
            notification_service = NotificationService(self.db)
            for job in high_match_jobs[:10]:  # Limit notifications
                await notification_service.create_notification(
                    user_id=scheduled_search.user_id,
                    type="new_job",
                    title=f"New Job Match: {job.title or 'Unknown'}",
                    message=f"A job matching your search '{scheduled_search.name}' was found.",
                    data={
                        "job_id": job.id,
                        "company": job.company,
                        "match_score": getattr(job, 'match_score', None),
                        "search_id": search_id
                    }
                )
        
        # Update last_run and calculate next_run
        scheduled_search.last_run = datetime.utcnow()
        scheduled_search.calculate_next_run()
        await self.db.commit()
        
        execution_time = time.time() - start_time
        
        return {
            "search_id": search_id,
            "jobs_found": len(unique_jobs),
            "high_match_count": len(high_match_jobs),
            "message": f"Search completed. Found {len(high_match_jobs)} high-match jobs.",
            "execution_time": execution_time
        }
    
    async def get_due_searches(self) -> List[ScheduledSearch]:
        """Get all scheduled searches that are due to run.
        
        Returns:
            List of due scheduled searches.
        """
        now = datetime.utcnow()
        
        query = select(ScheduledSearch).filter(
            and_(
                ScheduledSearch.is_active == True,
                ScheduledSearch.next_run <= now
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time format (HH:MM).
        
        Args:
            time_str: Time string to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                return False
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
