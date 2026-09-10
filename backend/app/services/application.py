from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationEvent
from app.models.job import Job
from app.models.user import User
from app.schemas.application import STATUS_PIPELINE, VALID_STATUSES


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_ownership(self, application_id: int, user_id: int) -> Application:
        result = await self.db.execute(
            select(Application).where(
                and_(Application.id == application_id, Application.user_id == user_id)
            )
        )
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return application

    async def _create_event(
        self,
        application_id: int,
        event_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ApplicationEvent:
        event = ApplicationEvent(
            application_id=application_id,
            event_type=event_type,
            old_value=old_value,
            new_value=new_value,
            description=description,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def create_application(
        self,
        user_id: int,
        job_id: int,
        resume_id: Optional[int] = None,
        cover_letter_id: Optional[int] = None,
        source: str = "manual",
        automation_mode: str = "manual",
        notes: Optional[str] = None,
    ) -> Application:
        job_result = await self.db.execute(select(Job).where(Job.id == job_id))
        if not job_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        existing = await self.db.execute(
            select(Application).where(
                and_(Application.user_id == user_id, Application.job_id == job_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application already exists for this job",
            )

        application = Application(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            cover_letter_id=cover_letter_id,
            status="saved",
            source=source,
            automation_mode=automation_mode,
            notes=notes,
        )
        self.db.add(application)
        await self.db.flush()
        await self.db.refresh(application)

        await self._create_event(
            application.id,
            "created",
            new_value="saved",
            description="Application created",
        )

        return application

    async def get_application(self, application_id: int, user_id: int) -> Application:
        return await self._verify_ownership(application_id, user_id)

    async def get_user_applications(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Application], int]:
        query = select(Application).where(Application.user_id == user_id)
        count_query = select(func.count(Application.id)).where(Application.user_id == user_id)

        if status_filter:
            query = query.where(Application.status == status_filter)
            count_query = count_query.where(Application.status == status_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Application.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        applications = list(result.scalars().all())

        return applications, total

    async def update_application(
        self, application_id: int, user_id: int, update_data: dict
    ) -> Application:
        application = await self._verify_ownership(application_id, user_id)

        for field, value in update_data.items():
            if value is not None and hasattr(application, field):
                setattr(application, field, value)

        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def update_application_status(
        self,
        application_id: int,
        user_id: int,
        new_status: str,
        notes: Optional[str] = None,
    ) -> Application:
        application = await self._verify_ownership(application_id, user_id)

        if new_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {new_status}",
            )

        allowed_next = STATUS_PIPELINE.get(application.status, [])
        if new_status not in allowed_next and new_status != application.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from '{application.status}' to '{new_status}'",
            )

        old_status = application.status
        application.status = new_status

        if new_status == "applied" and not application.applied_date:
            application.applied_date = datetime.utcnow()

        if notes:
            application.notes = notes

        await self._create_event(
            application.id,
            "status_change",
            old_value=old_status,
            new_value=new_status,
            description=f"Status changed from {old_status} to {new_status}",
        )

        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def save_application(
        self, user_id: int, job_id: int, notes: Optional[str] = None
    ) -> Application:
        return await self.create_application(
            user_id=user_id,
            job_id=job_id,
            notes=notes,
            source="manual",
        )

    async def mark_interested(self, user_id: int, job_id: int) -> Application:
        existing = await self.db.execute(
            select(Application).where(
                and_(Application.user_id == user_id, Application.job_id == job_id)
            )
        )
        application = existing.scalar_one_or_none()

        if not application:
            application = await self.create_application(
                user_id=user_id,
                job_id=job_id,
                source="manual",
            )

        if application.status == "saved":
            application = await self.update_application_status(
                application.id, user_id, "interested"
            )

        return application

    async def submit_application(
        self, application_id: int, user_id: int, submission_data: dict
    ) -> Application:
        application = await self._verify_ownership(application_id, user_id)

        submission_url = submission_data.get("submission_url")
        notes = submission_data.get("notes")

        if submission_url:
            application.submission_url = submission_url

        if notes:
            application.notes = notes

        if application.status not in ["ready_to_apply", "applied"]:
            application = await self.update_application_status(
                application_id, user_id, "application_submitted"
            )
        else:
            application = await self.update_application_status(
                application_id, user_id, "application_submitted"
            )

        return application

    async def withdraw_application(
        self, application_id: int, user_id: int
    ) -> Application:
        return await self.update_application_status(
            application_id, user_id, "withdrawn"
        )

    async def add_note(
        self, application_id: int, user_id: int, note: str
    ) -> ApplicationEvent:
        await self._verify_ownership(application_id, user_id)

        event = await self._create_event(
            application_id,
            "note_added",
            description=note,
        )

        result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        application = result.scalar_one()
        if application.notes:
            application.notes = f"{application.notes}\n\n{note}"
        else:
            application.notes = note

        await self.db.flush()
        return event

    async def schedule_follow_up(
        self, application_id: int, user_id: int, follow_up_date: datetime
    ) -> Application:
        application = await self._verify_ownership(application_id, user_id)
        application.next_follow_up = follow_up_date

        await self._create_event(
            application_id,
            "follow_up_scheduled",
            new_value=follow_up_date.isoformat(),
            description=f"Follow-up scheduled for {follow_up_date.strftime('%Y-%m-%d %H:%M')}",
        )

        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def get_upcoming_follow_ups(self, user_id: int) -> List[Application]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Application).where(
                and_(
                    Application.user_id == user_id,
                    Application.next_follow_up.isnot(None),
                    Application.next_follow_up >= now,
                    Application.status.notin_(["rejected", "withdrawn"]),
                )
            ).order_by(Application.next_follow_up.asc())
        )
        return list(result.scalars().all())

    async def get_application_stats(self, user_id: int) -> dict:
        total_result = await self.db.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        total_applications = total_result.scalar() or 0

        status_result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}

        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        week_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= week_start,
                )
            )
        )
        applications_this_week = week_result.scalar() or 0

        month_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= month_start,
                )
            )
        )
        applications_this_month = month_result.scalar() or 0

        conversion_rates = {}
        if total_applications > 0:
            for s in VALID_STATUSES:
                count = by_status.get(s, 0)
                conversion_rates[s] = round(count / total_applications * 100, 1)

        return {
            "total_applications": total_applications,
            "by_status": by_status,
            "conversion_rates": conversion_rates,
            "applications_this_week": applications_this_week,
            "applications_this_month": applications_this_month,
        }

    async def get_pipeline(self, user_id: int) -> dict:
        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        pipeline = {row[0]: row[1] for row in result.all()}

        total = sum(pipeline.values())

        for s in VALID_STATUSES:
            if s not in pipeline:
                pipeline[s] = 0

        return {"pipeline": pipeline, "total": total}

    async def get_application_events(
        self, application_id: int, user_id: int
    ) -> List[ApplicationEvent]:
        await self._verify_ownership(application_id, user_id)

        result = await self.db.execute(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == application_id)
            .order_by(ApplicationEvent.created_at.desc())
        )
        return list(result.scalars().all())
