import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobSearchParams,
    JobMatchResponse,
    SavedJobCreate,
    SavedJobResponse,
    JobStatsResponse,
)
from app.services.job import JobService

router = APIRouter()


@router.post("/search", response_model=JobListResponse)
async def search_jobs(
    params: JobSearchParams,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    job_service = JobService(db)
    jobs, total = await job_service.search_jobs(
        user_id=current_user.id, params=params
    )
    total_pages = math.ceil(total / params.page_size) if params.page_size > 0 else 0
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    job_service = JobService(db)
    params = JobSearchParams(page=page, page_size=page_size)
    jobs, total = await job_service.search_jobs(
        user_id=current_user.id, params=params
    )
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/saved", response_model=List[SavedJobResponse])
async def get_saved_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SavedJobResponse]:
    job_service = JobService(db)
    saved_jobs = await job_service.get_saved_jobs(user_id=current_user.id)
    return [SavedJobResponse.model_validate(sj) for sj in saved_jobs]


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatsResponse:
    job_service = JobService(db)
    stats = await job_service.get_job_stats(user_id=current_user.id)
    return JobStatsResponse(**stats)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job_service = JobService(db)
    job = await job_service.get_job(job_id=job_id)
    return JobResponse.model_validate(job)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job_service = JobService(db)
    job = await job_service.create_job(data=data)
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    job_service = JobService(db)
    job = await job_service.get_job(job_id=job_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    await db.flush()
    await db.refresh(job)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    job_service = JobService(db)
    job = await job_service.get_job(job_id=job_id)
    await db.delete(job)
    await db.flush()


@router.post("/{job_id}/save", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: int,
    data: SavedJobCreate = SavedJobCreate(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedJobResponse:
    job_service = JobService(db)
    saved_job = await job_service.save_job(
        user_id=current_user.id,
        job_id=job_id,
        notes=data.notes,
    )
    return SavedJobResponse.model_validate(saved_job)


@router.delete("/{job_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    job_service = JobService(db)
    success = await job_service.unsave_job(
        user_id=current_user.id,
        job_id=job_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved job not found",
        )


@router.post("/{job_id}/match", response_model=JobMatchResponse, status_code=status.HTTP_201_CREATED)
async def calculate_match(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobMatchResponse:
    job_service = JobService(db)
    match = await job_service.calculate_match_score(
        user_id=current_user.id,
        job_id=job_id,
    )
    return JobMatchResponse.model_validate(match)
