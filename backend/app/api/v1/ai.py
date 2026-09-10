import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    TailorResumeRequest,
    TailoredResumeResponse,
    CoverLetterRequest,
    CoverLetterRegenerateRequest,
    CoverLetterResponse,
    SkillGapRequest,
    SkillGapResponse,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
    ApplicationAnswersRequest,
    ApplicationAnswersResponse,
    ExtractKeywordsRequest,
    ExtractKeywordsResponse,
    CompanyAnalysisRequest,
    CompanyAnalysisResponse,
)
from app.services.ai.job_analysis import JobAnalysisService
from app.services.ai.resume_tailoring import ResumeTailoringService
from app.services.ai.cover_letter import CoverLetterService
from app.services.ai.skill_gap import SkillGapService
from app.services.ai.interview_prep import InterviewPreparationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-job", response_model=JobAnalysisResponse)
async def analyze_job(
    request: JobAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobAnalysisResponse:
    """Analyze a job description and extract structured data"""
    try:
        service = JobAnalysisService(db)
        result = await service.analyze_job_description(request.job_description)
        return JobAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Job analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job analysis failed: {str(e)}",
        )


@router.post("/tailor-resume", response_model=TailoredResumeResponse)
async def tailor_resume(
    request: TailorResumeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TailoredResumeResponse:
    """Tailor a resume for a specific job posting"""
    try:
        service = ResumeTailoringService(db)
        result = await service.tailor_resume_for_job(
            user_id=current_user.id,
            resume_id=request.resume_id,
            job_id=request.job_id,
        )
        return TailoredResumeResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Resume tailoring failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume tailoring failed: {str(e)}",
        )


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CoverLetterResponse:
    """Generate a personalized cover letter"""
    try:
        service = CoverLetterService(db)
        cover_letter = await service.generate_cover_letter(
            user_id=current_user.id,
            resume_id=request.resume_id,
            job_id=request.job_id,
        )
        return CoverLetterResponse(
            cover_letter=cover_letter,
            job_id=request.job_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation failed: {str(e)}",
        )


@router.post("/cover-letter/regenerate", response_model=CoverLetterResponse)
async def regenerate_cover_letter(
    request: CoverLetterRegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CoverLetterResponse:
    """Regenerate cover letter with user feedback"""
    try:
        service = CoverLetterService(db)
        cover_letter = await service.regenerate_cover_letter(
            user_id=current_user.id,
            job_id=request.job_id,
            feedback=request.feedback,
        )
        return CoverLetterResponse(
            cover_letter=cover_letter,
            job_id=request.job_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Cover letter regeneration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter regeneration failed: {str(e)}",
        )


@router.post("/skill-gap", response_model=SkillGapResponse)
async def analyze_skill_gap(
    request: SkillGapRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillGapResponse:
    """Analyze skill gaps between user profile and target role"""
    try:
        service = SkillGapService(db)
        result = await service.analyze_skill_gap(
            user_id=current_user.id,
            target_role=request.target_role,
        )
        return SkillGapResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Skill gap analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill gap analysis failed: {str(e)}",
        )


@router.post("/interview-questions", response_model=InterviewQuestionsResponse)
async def generate_interview_questions(
    request: InterviewQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewQuestionsResponse:
    """Generate interview preparation questions"""
    try:
        service = InterviewPreparationService(db)
        questions = await service.generate_interview_questions(
            job_id=request.job_id,
            resume_id=request.resume_id,
        )
        return InterviewQuestionsResponse(
            questions=questions,
            job_id=request.job_id,
            resume_id=request.resume_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Interview question generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview question generation failed: {str(e)}",
        )


@router.post("/application-answers", response_model=ApplicationAnswersResponse)
async def generate_application_answers(
    request: ApplicationAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationAnswersResponse:
    """Generate answers to job application questions"""
    try:
        from app.models.profile import Profile
        from app.models.job import Job
        from sqlalchemy import select

        profile_result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )

        job_result = await db.execute(select(Job).where(Job.id == request.job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        from app.services.ai.factory import AIProviderFactory
        ai_provider = AIProviderFactory.create()

        profile_data = {
            "name": profile.name,
            "current_title": profile.current_title,
            "skills": profile.skills or [],
            "technical_skills": profile.technical_skills or [],
            "years_of_experience": profile.years_of_experience,
            "education": profile.education or [],
            "job_history": profile.job_history or [],
        }

        job_data = {
            "title": job.title,
            "company": job.company,
            "required_skills": job.required_skills or [],
            "responsibilities": job.responsibilities or [],
            "qualifications": job.qualifications or [],
        }

        answers = await ai_provider.generate_application_answers(
            profile_data=profile_data,
            job_data=job_data,
            questions=request.questions,
        )

        return ApplicationAnswersResponse(
            answers=answers,
            job_id=request.job_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application answer generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application answer generation failed: {str(e)}",
        )


@router.post("/extract-keywords", response_model=ExtractKeywordsResponse)
async def extract_keywords(
    request: ExtractKeywordsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractKeywordsResponse:
    """Extract important keywords from job description"""
    try:
        service = JobAnalysisService(db)
        keywords = await service.extract_keywords(request.job_description)
        return ExtractKeywordsResponse(
            keywords=keywords,
            count=len(keywords),
        )
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword extraction failed: {str(e)}",
        )


@router.post("/company-analysis", response_model=CompanyAnalysisResponse)
async def analyze_company(
    request: CompanyAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyAnalysisResponse:
    """Analyze company information"""
    try:
        service = JobAnalysisService(db)
        result = await service.analyze_company_info(request.company_name)
        return CompanyAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Company analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Company analysis failed: {str(e)}",
        )
