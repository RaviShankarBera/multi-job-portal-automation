import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import Profile
from app.models.resume import Resume, ResumeVersion
from app.models.job import Job
from app.services.ai.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class ResumeTailoringService:
    """Service for AI-powered resume tailoring"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIProviderFactory.create()

    async def tailor_resume_for_job(
        self, user_id: int, resume_id: int, job_id: int
    ) -> Dict[str, Any]:
        """Tailor a resume for a specific job posting"""
        logger.info(f"Tailoring resume {resume_id} for job {job_id} (user: {user_id})")

        user = await self._get_user(user_id)
        profile = await self._get_profile(user_id)
        resume = await self._get_resume(resume_id, user_id)
        job = await self._get_job(job_id)

        resume_data = self._serialize_resume(resume)
        job_data = self._serialize_job(job)
        profile_data = self._serialize_profile(profile)

        tailored = await self.ai_provider.tailor_resume(resume_data, job_data, profile_data)

        version = await self._save_tailored_version(
            resume_id=resume_id,
            job_id=job_id,
            tailored_content=tailored,
            ats_score=tailored.get("ats_score"),
        )

        return {
            "version_id": version.id,
            "tailored_content": tailored,
            "original_ats_score": tailored.get("original_vs_tailored", {}).get("original_ats_score"),
            "tailored_ats_score": tailored.get("ats_score"),
            "changes_made": tailored.get("changes_made", []),
            "original_vs_tailored": tailored.get("original_vs_tailored", {}),
        }

    async def generate_professional_summary(self, profile: Profile, job: Job) -> str:
        """Generate an optimized professional summary"""
        resume_data = self._serialize_profile(profile)
        job_data = self._serialize_job(job)

        messages = [
            {
                "role": "system",
                "content": (
                    "Generate a concise professional summary (2-3 sentences) that highlights "
                    "the most relevant experience for this specific job. "
                    "Return ONLY the summary text, no JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PROFILE: {json.dumps(resume_data, default=str)}\n"
                    f"JOB: {json.dumps(job_data, default=str)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=200,
        )
        return self.ai_provider._extract_content(result)

    async def optimize_skills_section(
        self, skills: List[str], job_keywords: List[str]
    ) -> List[str]:
        """Reorder skills to prioritize job-matching keywords"""
        job_set = set(kw.lower() for kw in job_keywords)
        matching = [s for s in skills if s.lower() in job_set]
        non_matching = [s for s in skills if s.lower() not in job_set]
        return matching + non_matching

    async def improve_experience_bullets(
        self, experience: List[Dict], job_requirements: List[str]
    ) -> List[Dict]:
        """Improve experience bullets to match job requirements"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Improve these experience bullets to better match job requirements. "
                    "Rules:\n"
                    "- Do NOT add false achievements\n"
                    "- DO rephrase existing content for clarity and impact\n"
                    "- Add quantifiable metrics where reasonable from existing data\n"
                    "- Use strong action verbs\n"
                    "Return a JSON array of improved experience objects."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"EXPERIENCE:\n{json.dumps(experience, default=str)}\n\n"
                    f"JOB REQUIREMENTS:\n{json.dumps(job_requirements)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        parsed = self.ai_provider._parse_json_response(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("experience", experience)

    async def add_keywords_to_resume(
        self, resume_content: str, keywords: List[str]
    ) -> str:
        """Naturally integrate keywords into resume content"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Integrate these keywords naturally into the resume content. "
                    "Rules:\n"
                    "- Do NOT fabricate experience\n"
                    "- Only rephrase existing content to include keywords where appropriate\n"
                    "- Maintain natural language flow\n"
                    "Return the improved resume content."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"RESUME:\n{resume_content}\n\n"
                    f"KEYWORDS TO ADD: {json.dumps(keywords)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.4,
            max_tokens=3000,
        )
        return self.ai_provider._extract_content(result)

    async def _get_user(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

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

    def _serialize_resume(self, resume: Resume) -> Dict:
        return {
            "id": resume.id,
            "title": resume.title,
            "parsed_content": resume.parsed_content,
            "structured_data": resume.structured_data or {},
            "tags": resume.tags or [],
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
            "preferred_skills": job.preferred_skills or [],
            "responsibilities": job.responsibilities or [],
            "qualifications": job.qualifications or [],
            "experience_years": job.experience_years,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "employment_type": job.employment_type,
        }

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
            "soft_skills": profile.soft_skills or [],
            "certifications": profile.certifications or [],
            "education": profile.education or [],
            "companies_worked": profile.companies_worked or [],
            "job_history": profile.job_history or [],
        }

    async def _save_tailored_version(
        self,
        resume_id: int,
        job_id: int,
        tailored_content: Dict,
        ats_score: Optional[float],
    ) -> ResumeVersion:
        result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        next_version = (last_version.version_number + 1) if last_version else 1

        version = ResumeVersion(
            resume_id=resume_id,
            version_number=next_version,
            tailored_content=tailored_content,
            job_id=job_id,
            ats_score=ats_score,
        )
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        logger.info(f"Saved tailored resume version {next_version} for resume {resume_id}")
        return version
