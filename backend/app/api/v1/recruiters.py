from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.application import (
    RecruiterCreate,
    RecruiterUpdate,
    RecruiterResponse,
    CommunicationCreate,
    CommunicationResponse,
)
from app.services.recruiter import RecruiterService

router = APIRouter()


@router.post(
    "/", response_model=RecruiterResponse, status_code=status.HTTP_201_CREATED
)
async def create_recruiter(
    data: RecruiterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecruiterResponse:
    service = RecruiterService(db)
    recruiter = await service.create_recruiter(
        user_id=current_user.id, data=data
    )
    return RecruiterResponse.model_validate(recruiter)


@router.get("/", response_model=List[RecruiterResponse])
async def list_recruiters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RecruiterResponse]:
    service = RecruiterService(db)
    recruiters = await service.get_user_recruiters(user_id=current_user.id)
    return [RecruiterResponse.model_validate(r) for r in recruiters]


@router.get("/{recruiter_id}", response_model=RecruiterResponse)
async def get_recruiter(
    recruiter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecruiterResponse:
    service = RecruiterService(db)
    recruiter = await service.get_recruiter(
        recruiter_id=recruiter_id, user_id=current_user.id
    )
    return RecruiterResponse.model_validate(recruiter)


@router.put("/{recruiter_id}", response_model=RecruiterResponse)
async def update_recruiter(
    recruiter_id: int,
    data: RecruiterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecruiterResponse:
    service = RecruiterService(db)
    recruiter = await service.update_recruiter(
        recruiter_id=recruiter_id, user_id=current_user.id, data=data
    )
    return RecruiterResponse.model_validate(recruiter)


@router.delete("/{recruiter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recruiter(
    recruiter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = RecruiterService(db)
    await service.delete_recruiter(
        recruiter_id=recruiter_id, user_id=current_user.id
    )


@router.post(
    "/{recruiter_id}/communications",
    response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_communication(
    recruiter_id: int,
    data: CommunicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommunicationResponse:
    service = RecruiterService(db)
    communication = await service.add_communication(
        recruiter_id=recruiter_id, user_id=current_user.id, data=data
    )
    return CommunicationResponse.model_validate(communication)


@router.get(
    "/{recruiter_id}/communications",
    response_model=List[CommunicationResponse],
)
async def get_communications(
    recruiter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CommunicationResponse]:
    service = RecruiterService(db)
    communications = await service.get_communications(
        recruiter_id=recruiter_id, user_id=current_user.id
    )
    return [CommunicationResponse.model_validate(c) for c in communications]
