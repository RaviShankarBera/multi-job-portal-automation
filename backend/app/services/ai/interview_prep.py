import json
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import Profile
from app.models.resume import Resume
from app.models.job import Job
from app.services.ai.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class InterviewPreparationService:
    """Service for AI-powered interview preparation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIProviderFactory.create()

    async def generate_interview_questions(
        self, job_id: int, resume_id: int
    ) -> List[Dict[str, Any]]:
        """Generate tailored interview questions"""
        logger.info(f"Generating interview questions for job {job_id}")

        job = await self._get_job(job_id)
        resume = await self._get_resume(resume_id)

        job_data = self._serialize_job(job)
        resume_data = self._serialize_resume(resume)

        questions = await self.ai_provider.generate_interview_questions(
            job_data=job_data,
            resume_data=resume_data,
        )

        logger.info(f"Generated {len(questions)} interview questions")
        return questions

    async def generate_technical_questions(
        self, skills: List[str], job_requirements: List[str]
    ) -> List[Dict[str, str]]:
        """Generate technical interview questions based on skills"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Generate 10 technical interview questions based on these skills "
                    "and job requirements. Include a mix of:\n"
                    "- Conceptual questions\n"
                    "- Coding/problem-solving questions\n"
                    "- System design questions\n"
                    "- Best practices questions\n"
                    "Return a JSON array with question, category, difficulty, "
                    "and tips for each. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"SKILLS: {json.dumps(skills)}\n"
                    f"JOB REQUIREMENTS: {json.dumps(job_requirements)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        parsed = self.ai_provider._parse_json_response(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("questions", [])

    async def generate_behavioral_questions(
        self, profile: Dict, job_requirements: List[str]
    ) -> List[Dict[str, str]]:
        """Generate behavioral interview questions"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Generate 8 behavioral interview questions based on the candidate's "
                    "profile and job requirements. Include questions about:\n"
                    "- Leadership and teamwork\n"
                    "- Conflict resolution\n"
                    "- Problem-solving under pressure\n"
                    "- Adaptability and learning\n"
                    "- Achievement and motivation\n"
                    "Return a JSON array with question, category, difficulty, "
                    "and tips for each. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PROFILE: {json.dumps(profile, default=str)}\n"
                    f"JOB REQUIREMENTS: {json.dumps(job_requirements)}"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        parsed = self.ai_provider._parse_json_response(content)
        if isinstance(parsed, list):
            return parsed
        return parsed.get("questions", [])

    async def generate_company_research_prompt(self, company_name: str) -> str:
        """Generate a research prompt for company preparation"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Generate a structured research guide for preparing for an interview "
                    "at this company. Include sections for:\n"
                    "- Company overview and mission\n"
                    "- Recent news and developments\n"
                    "- Company culture and values\n"
                    "- Products/services\n"
                    "- Competitors\n"
                    "- Interview tips specific to this company\n"
                    "Format as a clear, actionable guide."
                ),
            },
            {
                "role": "user",
                "content": f"Generate interview preparation research for: {company_name}",
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
        )

        return self.ai_provider._extract_content(result)

    async def _get_job(self, job_id: int) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job

    async def _get_resume(self, resume_id: int) -> Resume:
        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")
        return resume

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
            "employment_type": job.employment_type,
        }

    def _serialize_resume(self, resume: Resume) -> Dict:
        return {
            "id": resume.id,
            "title": resume.title,
            "parsed_content": resume.parsed_content,
            "structured_data": resume.structured_data or {},
        }
