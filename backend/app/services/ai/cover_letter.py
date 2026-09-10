import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.job import Job
from app.services.ai.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class CoverLetterService:
    """Service for AI-powered cover letter generation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIProviderFactory.create()

    async def generate_cover_letter(
        self, user_id: int, resume_id: int, job_id: int
    ) -> str:
        """Generate a personalized cover letter"""
        logger.info(f"Generating cover letter for user {user_id}, job {job_id}")

        profile = await self._get_profile(user_id)
        resume = await self._get_resume(resume_id, user_id)
        job = await self._get_job(job_id)

        profile_data = self._serialize_profile(profile)
        resume_data = self._serialize_resume(resume)
        job_data = self._serialize_job(job)

        cover_letter = await self.ai_provider.generate_cover_letter(
            profile_data=profile_data,
            resume_data=resume_data,
            job_data=job_data,
        )

        logger.info(f"Cover letter generated successfully for job {job_id}")
        return cover_letter

    async def regenerate_cover_letter(
        self, user_id: int, job_id: int, feedback: str
    ) -> str:
        """Regenerate cover letter with user feedback"""
        logger.info(f"Regenerating cover letter with feedback for user {user_id}")

        profile = await self._get_profile(user_id)
        job = await self._get_job(job_id)

        profile_data = self._serialize_profile(profile)
        job_data = self._serialize_job(job)

        messages = [
            {
                "role": "system",
                "content": (
                    "Generate a professional cover letter based on the profile and job. "
                    "Incorporate the following feedback:\n"
                    f"{feedback}\n\n"
                    "Rules:\n"
                    "- Be specific to the job and company\n"
                    "- Highlight relevant experience\n"
                    "- Show enthusiasm and cultural fit\n"
                    "- Keep it under 400 words\n"
                    "- Use professional tone\n"
                    "- DO NOT fabricate achievements\n"
                    "Return ONLY the cover letter text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PROFILE:\n{json.dumps(profile_data, default=str)}\n\n"
                    f"JOB:\n{json.dumps(job_data, default=str)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return self.ai_provider._extract_content(result)

    async def format_cover_letter(
        self, content: str, recipient_info: Optional[Dict[str, str]] = None
    ) -> str:
        """Format cover letter with recipient info and proper structure"""
        if not recipient_info:
            return content

        recipient_name = recipient_info.get("name", "Hiring Manager")
        company_name = recipient_info.get("company", "")
        position = recipient_info.get("position", "")
        date = recipient_info.get("date", "")

        formatted = f"""{date if date else ''}

{recipient_name}
{company_name}
{position if position else ''}

{content}"""

        return formatted.strip()

    async def _get_profile(self, user_id: int) -> Profile:
        result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        return profile

    async def _get_resume(self, resume_id: int, user_id: int) -> Resume:
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found for user {user_id}")
        return resume

    async def _get_job(self, job_id: int) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job

    def _serialize_profile(self, profile: Profile) -> Dict:
        return {
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "current_title": profile.current_title,
            "target_title": profile.target_title,
            "years_of_experience": profile.years_of_experience,
            "skills": profile.skills or [],
            "technical_skills": profile.technical_skills or [],
            "education": profile.education or [],
            "companies_worked": profile.companies_worked or [],
            "job_history": profile.job_history or [],
        }

    def _serialize_resume(self, resume: Resume) -> Dict:
        return {
            "id": resume.id,
            "title": resume.title,
            "parsed_content": resume.parsed_content,
            "structured_data": resume.structured_data or {},
        }

    def _serialize_job(self, job: Job) -> Dict:
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_status": job.remote_status,
            "description": job.description,
            "required_skills": job.required_skills or [],
            "responsibilities": job.responsibilities or [],
            "qualifications": job.qualifications or [],
            "experience_years": job.experience_years,
        }
