import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import Profile
from app.models.job import Job
from app.services.ai.factory import AIProviderFactory

logger = logging.getLogger(__name__)


class SkillGapService:
    """Service for AI-powered skill gap analysis"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = AIProviderFactory.create()

    async def analyze_skill_gap(
        self, user_id: int, target_role: str
    ) -> Dict[str, Any]:
        """Analyze skill gaps between user and target role"""
        logger.info(f"Analyzing skill gap for user {user_id}, target: {target_role}")

        profile = await self._get_profile(user_id)
        user_skills = self._extract_user_skills(profile)

        market_skills = await self.get_market_skills(target_role, profile.location)

        if not market_skills:
            market_skills = await self._get_market_skills_from_jobs(target_role)

        result = await self.ai_provider.analyze_skill_gap(
            user_skills=user_skills,
            job_market_skills=market_skills,
        )

        result["target_role"] = target_role
        result["user_skills_count"] = len(user_skills)
        result["market_skills_count"] = len(market_skills)

        logger.info(
            f"Skill gap analysis complete: {len(result.get('missing_skills', []))} missing skills"
        )
        return result

    async def get_market_skills(
        self, target_role: str, location: Optional[str] = None
    ) -> List[str]:
        """Get in-demand skills for a target role from job market"""
        cache_key = f"market_skills:{target_role}:{location or 'global'}"

        messages = [
            {
                "role": "system",
                "content": (
                    f"List the top 20-30 most in-demand skills for a '{target_role}' position"
                    f"{' in ' + location if location else ''}. "
                    "Include both technical and soft skills. "
                    "Return a JSON array of skill names. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"What are the most sought-after skills for a {target_role} role"
                    f"{' in ' + location if location else ''}?"
                ),
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        parsed = self.ai_provider._parse_json_response(content)

        if isinstance(parsed, list):
            return parsed
        return parsed.get("skills", parsed.get("keywords", []))

    async def get_skill_demand_stats(self, skill_list: List[str]) -> Dict[str, Any]:
        """Get demand statistics for a list of skills"""
        messages = [
            {
                "role": "system",
                "content": (
                    "Provide demand statistics for these skills in the current job market. "
                    "Return a JSON object where each skill maps to:\n"
                    "- demand_level: 'high', 'medium', or 'low'\n"
                    "- growth_trend: 'increasing', 'stable', or 'decreasing'\n"
                    "- average_salary_impact: estimated salary increase percentage\n"
                    "- industries: top industries using this skill\n"
                    "Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze demand for: {json.dumps(skill_list)}",
            },
        ]

        result = await self.ai_provider._call_openai(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = self.ai_provider._extract_content(result)
        return self.ai_provider._parse_json_response(content)

    async def _get_market_skills_from_jobs(self, target_role: str) -> List[str]:
        """Fallback: extract skills from collected jobs"""
        result = await self.db.execute(
            select(Job)
            .where(Job.title.ilike(f"%{target_role}%"))
            .limit(20)
        )
        jobs = result.scalars().all()

        all_skills = set()
        for job in jobs:
            if job.required_skills:
                if isinstance(job.required_skills, list):
                    all_skills.update(job.required_skills)
            if job.preferred_skills:
                if isinstance(job.preferred_skills, list):
                    all_skills.update(job.preferred_skills)

        return list(all_skills) if all_skills else []

    def _extract_user_skills(self, profile: Profile) -> List[str]:
        """Extract all skills from user profile"""
        skills = set()
        if profile.skills:
            skills.update(profile.skills)
        if profile.technical_skills:
            skills.update(profile.technical_skills)
        if profile.soft_skills:
            skills.update(profile.soft_skills)
        return list(skills)

    async def _get_profile(self, user_id: int) -> Profile:
        result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Profile not found for user {user_id}")
        return profile
