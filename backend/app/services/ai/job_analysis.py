import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.services.ai.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class JobAnalysisService:
    """Service for AI-powered job description analysis"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIProviderFactory.create()

    async def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze a job description and extract structured data"""
        logger.info("Analyzing job description")

        result = await self.ai_provider.analyze_job_description(job_description)

        result.setdefault("title", "")
        result.setdefault("company", "")
        result.setdefault("required_skills", [])
        result.setdefault("preferred_skills", [])
        result.setdefault("experience_years", None)
        result.setdefault("responsibilities", [])
        result.setdefault("qualifications", [])
        result.setdefault("salary_range", None)
        result.setdefault("remote_status", None)
        result.setdefault("employment_type", "full-time")
        result.setdefault("industry", "")
        result.setdefault("key_requirements", "")

        return result

    async def extract_keywords(self, job_description: str) -> List[str]:
        """Extract important keywords from job description"""
        logger.info("Extracting keywords from job description")
        return await self.ai_provider.extract_job_keywords(job_description)

    async def analyze_company_info(self, company_name: str) -> Dict[str, Any]:
        """Analyze company information"""
        logger.info(f"Analyzing company info: {company_name}")

        messages = [
            {
                "role": "system",
                "content": (
                    "Provide comprehensive company information. Return a JSON object with:\n"
                    "- overview: company description\n"
                    "- industry: primary industry\n"
                    "- size: company size category\n"
                    "- founded: founding year if known\n"
                    "- headquarters: location\n"
                    "- culture: work culture description\n"
                    "- benefits: common benefits offered\n"
                    "- recent_news: any notable recent developments\n"
                    "- glassdoor_rating: estimated rating if known\n"
                    "Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Provide information about: {company_name}",
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        return self.ai_provider._parse_json_response(content)

    async def analyze_job_from_db(self, job_id: int) -> Dict[str, Any]:
        """Analyze a job from the database"""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.description:
            analysis = await self.analyze_job_description(job.description)
        else:
            analysis = {
                "title": job.title,
                "company": job.company,
                "required_skills": job.required_skills or [],
                "preferred_skills": job.preferred_skills or [],
                "experience_years": job.experience_years,
                "responsibilities": job.responsibilities or [],
                "qualifications": job.qualifications or [],
                "salary_range": {
                    "min": job.salary_min,
                    "max": job.salary_max,
                    "currency": job.salary_currency,
                } if job.salary_min else None,
                "remote_status": job.remote_status,
                "employment_type": job.employment_type,
                "industry": "",
                "key_requirements": "",
            }

        analysis["job_id"] = job.id
        return analysis
