import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatusUpdate,
    ApplicationSubmitData,
    ApplicationNoteCreate,
    ApplicationFollowUpUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationEventResponse,
    ApplicationStatsResponse,
    PipelineResponse,
    FollowUpResponse,
)
from app.services.application import ApplicationService

router = APIRouter()


@router.post(
    "/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.create_application(
        user_id=current_user.id,
        job_id=data.job_id,
        resume_id=data.resume_id,
        cover_letter_id=data.cover_letter_id,
        source=data.source,
        automation_mode=data.automation_mode,
        notes=data.notes,
    )
    return ApplicationResponse.model_validate(application)


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationListResponse:
    service = ApplicationService(db)
    skip = (page - 1) * page_size
    applications, total = await service.get_user_applications(
        user_id=current_user.id,
        status_filter=status_filter,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return ApplicationListResponse(
        applications=[ApplicationResponse.model_validate(a) for a in applications],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=ApplicationStatsResponse)
async def get_application_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationStatsResponse:
    service = ApplicationService(db)
    stats = await service.get_application_stats(user_id=current_user.id)
    return ApplicationStatsResponse(**stats)


@router.get("/pipeline", response_model=PipelineResponse)
async def get_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PipelineResponse:
    service = ApplicationService(db)
    pipeline = await service.get_pipeline(user_id=current_user.id)
    return PipelineResponse(**pipeline)


@router.get("/follow-ups", response_model=FollowUpResponse)
async def get_follow_ups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpResponse:
    service = ApplicationService(db)
    applications = await service.get_upcoming_follow_ups(user_id=current_user.id)
    return FollowUpResponse(
        applications=[ApplicationResponse.model_validate(a) for a in applications],
        total=len(applications),
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.get_application(
        application_id=application_id, user_id=current_user.id
    )
    return ApplicationResponse.model_validate(application)


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    update_data = data.model_dump(exclude_unset=True)
    application = await service.update_application(
        application_id=application_id,
        user_id=current_user.id,
        update_data=update_data,
    )
    return ApplicationResponse.model_validate(application)


@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.update_application_status(
        application_id=application_id,
        user_id=current_user.id,
        new_status=data.status,
        notes=data.notes,
    )
    return ApplicationResponse.model_validate(application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = ApplicationService(db)
    await service.withdraw_application(
        application_id=application_id, user_id=current_user.id
    )


@router.post(
    "/{application_id}/submit", response_model=ApplicationResponse
)
async def submit_application(
    application_id: int,
    data: ApplicationSubmitData = ApplicationSubmitData(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.submit_application(
        application_id=application_id,
        user_id=current_user.id,
        submission_data=data.model_dump(),
    )
    return ApplicationResponse.model_validate(application)


@router.post(
    "/{application_id}/notes", response_model=ApplicationEventResponse
)
async def add_note(
    application_id: int,
    data: ApplicationNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationEventResponse:
    service = ApplicationService(db)
    event = await service.add_note(
        application_id=application_id,
        user_id=current_user.id,
        note=data.note,
    )
    return ApplicationEventResponse.model_validate(event)


@router.put(
    "/{application_id}/follow-up", response_model=ApplicationResponse
)
async def schedule_follow_up(
    application_id: int,
    data: ApplicationFollowUpUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    service = ApplicationService(db)
    application = await service.schedule_follow_up(
        application_id=application_id,
        user_id=current_user.id,
        follow_up_date=data.follow_up_date,
    )
    return ApplicationResponse.model_validate(application)


@router.get(
    "/{application_id}/events",
    response_model=list[ApplicationEventResponse],
)
async def get_application_events(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApplicationEventResponse]:
    service = ApplicationService(db)
    events = await service.get_application_events(
        application_id=application_id, user_id=current_user.id
    )
    return [ApplicationEventResponse.model_validate(e) for e in events]
