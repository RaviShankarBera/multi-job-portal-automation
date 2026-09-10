from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate, SkillsUpdate


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[Profile]:
        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, data: ProfileCreate) -> Profile:
        # Check if profile already exists
        existing = await self.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this user",
            )

        profile = Profile(user_id=user_id, **data.model_dump(exclude_unset=True))
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(self, user_id: int, data: ProfileUpdate) -> Optional[Profile]:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update_skills(self, user_id: int, data: SkillsUpdate) -> Optional[Profile]:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        profile.skills = data.skills
        if data.technical_skills is not None:
            profile.technical_skills = data.technical_skills
        if data.soft_skills is not None:
            profile.soft_skills = data.soft_skills

        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete(self, user_id: int) -> bool:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return False

        await self.db.delete(profile)
        await self.db.flush()
        return True