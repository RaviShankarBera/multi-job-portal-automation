from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, SkillsUpdate
from app.services.profile import ProfileService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    profile_service = ProfileService(db)
    profile = await profile_service.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    profile_service = ProfileService(db)
    profile = await profile_service.update(current_user.id, data)
    return profile


@router.post("/skills", response_model=ProfileResponse)
async def update_skills(
    data: SkillsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    profile_service = ProfileService(db)
    profile = await profile_service.update_skills(current_user.id, data)
    return profile