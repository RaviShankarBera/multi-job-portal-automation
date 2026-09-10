from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Recruiter, Communication, Application
from app.schemas.application import RecruiterCreate, RecruiterUpdate, CommunicationCreate


class RecruiterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _verify_ownership(self, recruiter_id: int, user_id: int) -> Recruiter:
        result = await self.db.execute(
            select(Recruiter).where(
                and_(Recruiter.id == recruiter_id, Recruiter.user_id == user_id)
            )
        )
        recruiter = result.scalar_one_or_none()
        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found",
            )
        return recruiter

    async def create_recruiter(self, user_id: int, data: RecruiterCreate) -> Recruiter:
        recruiter = Recruiter(
            user_id=user_id,
            name=data.name,
            company=data.company,
            email=data.email,
            phone=data.phone,
            linkedin_url=data.linkedin_url,
            role=data.role,
            source=data.source,
            notes=data.notes,
        )
        self.db.add(recruiter)
        await self.db.flush()
        await self.db.refresh(recruiter)
        return recruiter

    async def get_recruiter(self, recruiter_id: int, user_id: int) -> Recruiter:
        return await self._verify_ownership(recruiter_id, user_id)

    async def get_user_recruiters(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Recruiter]:
        result = await self.db.execute(
            select(Recruiter)
            .where(Recruiter.user_id == user_id)
            .order_by(Recruiter.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_recruiter(
        self, recruiter_id: int, user_id: int, data: RecruiterUpdate
    ) -> Recruiter:
        recruiter = await self._verify_ownership(recruiter_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(recruiter, field, value)

        await self.db.flush()
        await self.db.refresh(recruiter)
        return recruiter

    async def delete_recruiter(self, recruiter_id: int, user_id: int) -> bool:
        recruiter = await self._verify_ownership(recruiter_id, user_id)
        await self.db.delete(recruiter)
        await self.db.flush()
        return True

    async def link_to_application(
        self, recruiter_id: int, application_id: int, user_id: int
    ) -> bool:
        await self._verify_ownership(recruiter_id, user_id)

        app_result = await self.db.execute(
            select(Application).where(
                and_(Application.id == application_id, Application.user_id == user_id)
            )
        )
        application = app_result.scalar_one_or_none()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        return True

    async def add_communication(
        self, recruiter_id: int, user_id: int, data: CommunicationCreate
    ) -> Communication:
        await self._verify_ownership(recruiter_id, user_id)

        comm_date = data.communication_date or datetime.utcnow()

        communication = Communication(
            recruiter_id=recruiter_id,
            application_id=data.application_id,
            type=data.type,
            direction=data.direction,
            subject=data.subject,
            content=data.content,
            communication_date=comm_date,
        )
        self.db.add(communication)
        await self.db.flush()
        await self.db.refresh(communication)
        return communication

    async def get_communications(
        self, recruiter_id: int, user_id: int
    ) -> List[Communication]:
        await self._verify_ownership(recruiter_id, user_id)

        result = await self.db.execute(
            select(Communication)
            .where(Communication.recruiter_id == recruiter_id)
            .order_by(Communication.communication_date.desc())
        )
        return list(result.scalars().all())
