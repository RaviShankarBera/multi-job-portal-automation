from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.resume import (
    ResumeResponse,
    ResumeListResponse,
    ResumeVersionResponse,
    ResumeVersionCreate,
    ATSScoreResponse,
)
from app.services.resume import ResumeService
from app.models.user import User

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    title: Optional[str] = Query(None, description="Resume title"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume_service = ResumeService(db)
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    resume = await resume_service.upload_resume(
        user_id=current_user.id, file=file, title=title, tags=tag_list
    )
    return resume


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeListResponse:
    resume_service = ResumeService(db)
    resumes = await resume_service.get_resumes(user_id=current_user.id)
    return ResumeListResponse(resumes=resumes, total=len(resumes))


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume_service = ResumeService(db)
    resume = await resume_service.get_resume(resume_id=resume_id, user_id=current_user.id)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    resume_service = ResumeService(db)
    await resume_service.delete_resume(resume_id=resume_id, user_id=current_user.id)


@router.put("/{resume_id}/primary", response_model=ResumeResponse)
async def set_primary_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume_service = ResumeService(db)
    resume = await resume_service.set_primary_resume(resume_id=resume_id, user_id=current_user.id)
    return resume


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionResponse])
async def get_resume_versions(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeVersionResponse]:
    resume_service = ResumeService(db)
    versions = await resume_service.get_versions(resume_id=resume_id, user_id=current_user.id)
    return versions


@router.post("/{resume_id}/versions", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_resume_version(
    resume_id: int,
    data: ResumeVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    resume_service = ResumeService(db)
    version = await resume_service.create_version(
        resume_id=resume_id,
        user_id=current_user.id,
        job_id=data.job_id,
        tailored_content=data.tailored_content,
    )
    return version


@router.post("/{resume_id}/parse", response_model=ResumeResponse)
async def reparse_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume_service = ResumeService(db)
    resume = await resume_service.reparse_resume(resume_id=resume_id, user_id=current_user.id)
    return resume


@router.get("/{resume_id}/ats-score", response_model=ATSScoreResponse)
async def get_ats_score(
    resume_id: int,
    job_id: Optional[int] = Query(None, description="Job ID to score against"),
    job_description: Optional[str] = Query(None, description="Job description text"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ATSScoreResponse:
    if not job_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_description query parameter is required",
        )

    resume_service = ResumeService(db)
    ats_score = await resume_service.calculate_ats_score(
        resume_id=resume_id,
        user_id=current_user.id,
        job_description=job_description,
    )
    return ats_score
