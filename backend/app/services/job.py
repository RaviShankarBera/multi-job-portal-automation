import hashlib
import math
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.models.user import User
from app.models.profile import Profile
from app.schemas.job import (
    JobCreate, JobUpdate, JobSearchParams, SavedJobCreate
)
from app.services.matching import JobMatchingService


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_duplicate_hash(
        self, title: str, company: str, location: str
    ) -> str:
        normalized_title = title.strip().lower()
        normalized_company = company.strip().lower()
        normalized_location = location.strip().lower()
        raw = f"{normalized_title}|{normalized_company}|{normalized_location}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def check_duplicate(
        self, title: str, company: str, location: str
    ) -> Optional[Job]:
        job_hash = self.generate_duplicate_hash(title, company, location)
        result = await self.db.execute(
            select(Job).where(Job.duplicate_hash == job_hash)
        )
        return result.scalar_one_or_none()

    async def create_job(self, data: JobCreate) -> Job:
        existing = await self.check_duplicate(data.title, data.company, data.location)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate job found: {existing.title} at {existing.company}"
            )

        job_hash = self.generate_duplicate_hash(data.title, data.company, data.location)
        job = Job(
            source=data.source,
            source_id=data.source_id,
            url=data.url,
            title=data.title,
            company=data.company,
            location=data.location,
            remote_status=data.remote_status,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            salary_currency=data.salary_currency,
            experience_years=data.experience_years,
            employment_type=data.employment_type,
            description=data.description,
            required_skills=data.required_skills,
            preferred_skills=data.preferred_skills,
            responsibilities=data.responsibilities,
            qualifications=data.qualifications,
            posted_date=data.posted_date,
            application_url=data.application_url,
            status=data.status,
            duplicate_hash=job_hash,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def search_jobs(
        self, user_id: int, params: JobSearchParams
    ) -> tuple[List[Job], int]:
        query = select(Job)
        count_query = select(func.count(Job.id))

        filters = []

        if params.keywords:
            keyword_filter = or_(
                Job.title.ilike(f"%{params.keywords}%"),
                Job.description.ilike(f"%{params.keywords}%"),
                Job.company.ilike(f"%{params.keywords}%"),
            )
            filters.append(keyword_filter)

        if params.title:
            filters.append(Job.title.ilike(f"%{params.title}%"))

        if params.location:
            filters.append(Job.location.ilike(f"%{params.location}%"))

        if params.remote:
            filters.append(Job.remote_status == params.remote)

        if params.experience_min is not None:
            filters.append(Job.experience_years >= params.experience_min)

        if params.experience_max is not None:
            filters.append(Job.experience_years <= params.experience_max)

        if params.salary_min is not None:
            filters.append(Job.salary_max >= params.salary_min)

        if params.salary_max is not None:
            filters.append(Job.salary_min <= params.salary_max)

        if params.company:
            filters.append(Job.company.ilike(f"%{params.company}%"))

        if params.employment_type:
            filters.append(Job.employment_type == params.employment_type)

        if params.status:
            filters.append(Job.status == params.status)

        if params.source:
            filters.append(Job.source == params.source)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(Job.collected_date.desc())
        query = query.offset((params.page - 1) * params.page_size)
        query = query.limit(params.page_size)

        result = await self.db.execute(query)
        jobs = list(result.scalars().all())

        return jobs, total

    async def get_job(self, job_id: int) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job

    async def save_job(
        self, user_id: int, job_id: int, notes: Optional[str] = None
    ) -> SavedJob:
        job = await self.get_job(job_id)

        existing = await self.db.execute(
            select(SavedJob).where(
                and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job already saved"
            )

        saved_job = SavedJob(
            user_id=user_id,
            job_id=job_id,
            notes=notes,
        )
        self.db.add(saved_job)
        await self.db.flush()
        await self.db.refresh(saved_job)
        return saved_job

    async def unsave_job(self, user_id: int, job_id: int) -> bool:
        result = await self.db.execute(
            select(SavedJob).where(
                and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
            )
        )
        saved_job = result.scalar_one_or_none()
        if not saved_job:
            return False

        await self.db.delete(saved_job)
        await self.db.flush()
        return True

    async def get_saved_jobs(self, user_id: int) -> List[SavedJob]:
        result = await self.db.execute(
            select(SavedJob).where(SavedJob.user_id == user_id)
            .order_by(SavedJob.saved_at.desc())
        )
        return list(result.scalars().all())

    async def deduplicate_jobs(self, jobs: List[Job]) -> List[Job]:
        seen_hashes = set()
        unique_jobs = []
        for job in jobs:
            if job.duplicate_hash and job.duplicate_hash not in seen_hashes:
                seen_hashes.add(job.duplicate_hash)
                unique_jobs.append(job)
            elif not job.duplicate_hash:
                unique_jobs.append(job)
        return unique_jobs

    async def calculate_match_score(
        self, user_id: int, job_id: int
    ) -> JobMatch:
        job = await self.get_job(job_id)

        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        matching_service = JobMatchingService()

        user_skills = []
        user_experience_years = 0
        user_title = ""
        user_expected_salary = None
        user_location = ""
        user_remote_preference = ""
        user_certifications: List[str] = []

        if profile:
            user_skills = profile.skills or []
            user_experience_years = profile.years_of_experience or 0
            user_title = profile.target_title or profile.current_title or ""
            user_expected_salary = profile.expected_salary
            user_location = profile.location or ""
            user_remote_preference = profile.remote_preference or ""
            user_certifications = profile.certifications or []

        scores = {
            "skills_score": matching_service.calculate_skills_score(
                user_skills,
                job.required_skills or [],
                job.preferred_skills or [],
            ),
            "experience_score": matching_service.calculate_experience_score(
                user_experience_years,
                job.experience_years,
            ),
            "title_score": matching_service.calculate_title_score(
                user_title,
                job.title,
            ),
            "location_score": matching_service.calculate_location_score(
                user_location,
                job.location,
                job.remote_status,
                user_remote_preference,
            ),
            "salary_score": matching_service.calculate_salary_score(
                user_expected_salary,
                job.salary_min,
                job.salary_max,
            ),
            "industry_score": 50.0,
            "education_score": 50.0,
            "certification_score": matching_service.calculate_certification_score(
                user_certifications,
                job.qualifications or [],
            ),
        }

        overall_score = matching_service.calculate_overall_score(scores)
        explanation = matching_service.generate_explanation(scores)

        existing_result = await self.db.execute(
            select(JobMatch).where(
                and_(JobMatch.job_id == job_id, JobMatch.user_id == user_id)
            )
        )
        existing_match = existing_result.scalar_one_or_none()

        if existing_match:
            existing_match.overall_score = overall_score
            existing_match.skills_score = scores["skills_score"]
            existing_match.experience_score = scores["experience_score"]
            existing_match.title_score = scores["title_score"]
            existing_match.industry_score = scores["industry_score"]
            existing_match.location_score = scores["location_score"]
            existing_match.salary_score = scores["salary_score"]
            existing_match.education_score = scores["education_score"]
            existing_match.certification_score = scores["certification_score"]
            existing_match.explanation = explanation
            existing_match.calculated_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(existing_match)
            return existing_match

        match = JobMatch(
            job_id=job_id,
            user_id=user_id,
            overall_score=overall_score,
            skills_score=scores["skills_score"],
            experience_score=scores["experience_score"],
            title_score=scores["title_score"],
            industry_score=scores["industry_score"],
            location_score=scores["location_score"],
            salary_score=scores["salary_score"],
            education_score=scores["education_score"],
            certification_score=scores["certification_score"],
            explanation=explanation,
            calculated_at=datetime.utcnow(),
        )
        self.db.add(match)
        await self.db.flush()
        await self.db.refresh(match)
        return match

    async def get_job_stats(self, user_id: int) -> dict:
        total_result = await self.db.execute(select(func.count(Job.id)))
        total_jobs = total_result.scalar() or 0

        source_result = await self.db.execute(
            select(Job.source, func.count(Job.id)).group_by(Job.source)
        )
        jobs_by_source = {row[0]: row[1] for row in source_result.all()}

        status_result = await self.db.execute(
            select(Job.status, func.count(Job.id)).group_by(Job.status)
        )
        jobs_by_status = {row[0]: row[1] for row in status_result.all()}

        saved_result = await self.db.execute(
            select(func.count(SavedJob.id)).where(SavedJob.user_id == user_id)
        )
        saved_jobs_count = saved_result.scalar() or 0

        match_result = await self.db.execute(
            select(func.count(JobMatch.id)).where(JobMatch.user_id == user_id)
        )
        matched_jobs_count = match_result.scalar() or 0

        avg_result = await self.db.execute(
            select(func.avg(JobMatch.overall_score)).where(
                JobMatch.user_id == user_id
            )
        )
        average_match_score = avg_result.scalar()

        return {
            "total_jobs": total_jobs,
            "jobs_by_source": jobs_by_source,
            "jobs_by_status": jobs_by_status,
            "saved_jobs_count": saved_jobs_count,
            "matched_jobs_count": matched_jobs_count,
            "average_match_score": (
                round(average_match_score, 2) if average_match_score else None
            ),
        }
