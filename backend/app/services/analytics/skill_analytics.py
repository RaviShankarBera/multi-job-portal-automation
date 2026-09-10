import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.models.profile import Profile
from app.schemas.analytics import (
    SkillCoverageResponse,
    SkillCoverageItem,
    SkillRecommendation,
    SkillTrendsResponse,
    SkillTrendItem,
)


class SkillAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _cache_key(self, user_id: int, suffix: str) -> str:
        return f"analytics:skills:{user_id}:{suffix}"

    async def _get_cached(self, key: str) -> Optional[Any]:
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    async def _set_cached(self, key: str, data: Any, ttl: int = 600) -> None:
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            await redis.set(key, json.dumps(data, default=str), ex=ttl)
        except Exception:
            pass

    async def _get_user_skills(self, user_id: int) -> List[str]:
        result = await self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return []

        skills = set()
        if profile.skills:
            skills.update(s.strip().lower() for s in profile.skills)
        if profile.technical_skills:
            skills.update(s.strip().lower() for s in profile.technical_skills)
        return list(skills)

    async def _get_market_skill_counts(self) -> Dict[str, int]:
        result = await self.db.execute(select(Job.required_skills))
        skill_counts: Dict[str, int] = {}
        for row in result.scalars().all():
            if row:
                for skill in row:
                    normalized = skill.strip().lower()
                    skill_counts[normalized] = skill_counts.get(normalized, 0) + 1
        return skill_counts

    async def get_user_skill_coverage(self, user_id: int) -> SkillCoverageResponse:
        cache_key = self._cache_key(user_id, "coverage")
        cached = await self._get_cached(cache_key)
        if cached:
            return SkillCoverageResponse(**cached)

        user_skills = await self._get_user_skills(user_id)
        market_skills = await self._get_market_skill_counts()

        if not market_skills:
            return SkillCoverageResponse()

        total_demand = sum(market_skills.values())
        sorted_market = sorted(
            market_skills.items(), key=lambda x: x[1], reverse=True
        )[:50]

        user_skills_set = set(s.strip().lower() for s in user_skills)

        covered = []
        missing = []
        covered_count = 0

        for skill, count in sorted_market:
            percentage = round(count / total_demand * 100, 1)
            user_has = skill in user_skills_set

            if user_has:
                covered_count += 1

            importance = "high" if percentage > 5 else ("medium" if percentage > 2 else "low")

            item = SkillCoverageItem(
                skill=skill,
                user_has=user_has,
                market_demand=percentage,
                importance=importance,
            )

            if user_has:
                covered.append(item)
            else:
                missing.append(item)

        total_market = len(sorted_market)
        coverage_pct = (
            (covered_count / total_market * 100) if total_market > 0 else 0.0
        )

        result = SkillCoverageResponse(
            covered_skills=covered,
            missing_skills=missing,
            coverage_percentage=round(coverage_pct, 1),
            total_market_skills=total_market,
            user_skills_count=len(user_skills),
        )

        await self._set_cached(cache_key, result.model_dump())
        return result

    async def get_missing_skills(self, user_id: int) -> SkillCoverageResponse:
        return await self.get_user_skill_coverage(user_id)

    async def get_skill_recommendations(
        self, user_id: int
    ) -> List[SkillRecommendation]:
        cache_key = self._cache_key(user_id, "recommendations")
        cached = await self._get_cached(cache_key)
        if cached:
            return [SkillRecommendation(**item) for item in cached]

        user_skills = await self._get_user_skills(user_id)
        user_skills_set = set(s.strip().lower() for s in user_skills)

        market_skills = await self._get_market_skill_counts()
        if not market_skills:
            return []

        total_demand = sum(market_skills.values())

        result = await self.db.execute(
            select(Job.required_skills)
            .join(SavedJob, SavedJob.job_id == Job.id)
            .where(SavedJob.user_id == user_id)
        )
        saved_job_skills: Dict[str, int] = {}
        for row in result.scalars().all():
            if row:
                for skill in row:
                    normalized = skill.strip().lower()
                    saved_job_skills[normalized] = saved_job_skills.get(normalized, 0) + 1

        recommendations = []
        for skill, count in sorted(
            market_skills.items(), key=lambda x: x[1], reverse=True
        )[:30]:
            if skill in user_skills_set:
                continue

            demand_score = round(count / total_demand * 100, 1) if total_demand > 0 else 0.0
            saved_job_relevance = saved_job_skills.get(skill, 0)

            if demand_score > 5:
                priority = "high"
                reason = f"In high demand ({demand_score}% of jobs require this)"
            elif demand_score > 2 or saved_job_relevance > 2:
                priority = "medium"
                reason = f"Moderate demand ({demand_score}% of jobs)"
            else:
                priority = "low"
                reason = f"Growing skill ({demand_score}% of jobs)"

            if saved_job_relevance > 3:
                priority = "high"
                reason = f"Required by {saved_job_relevance} of your saved jobs"

            recommendations.append(
                SkillRecommendation(
                    skill=skill,
                    demand_score=demand_score,
                    priority=priority,
                    reason=reason,
                    jobs_requiring=count,
                )
            )

        recommendations.sort(
            key=lambda x: (
                {"high": 3, "medium": 2, "low": 1}.get(x.priority, 0),
                x.demand_score,
            ),
            reverse=True,
        )

        await self._set_cached(
            cache_key, [r.model_dump() for r in recommendations]
        )
        return recommendations[:15]

    async def get_skill_trends(self, user_id: int) -> SkillTrendsResponse:
        cache_key = self._cache_key(user_id, "trends")
        cached = await self._get_cached(cache_key)
        if cached:
            return SkillTrendsResponse(**cached)

        now = datetime.utcnow()
        recent_cutoff = now - timedelta(days=14)
        older_cutoff = now - timedelta(days=60)

        recent_result = await self.db.execute(
            select(Job.required_skills).where(Job.collected_date >= recent_cutoff)
        )
        recent_skills: List[str] = []
        for row in recent_result.scalars().all():
            if row:
                recent_skills.extend(row)

        older_result = await self.db.execute(
            select(Job.required_skills).where(
                and_(
                    Job.collected_date >= older_cutoff,
                    Job.collected_date < recent_cutoff,
                )
            )
        )
        older_skills: List[str] = []
        for row in older_result.scalars().all():
            if row:
                older_skills.extend(row)

        def count_skills(skills: List[str]) -> Dict[str, int]:
            counts: Dict[str, int] = {}
            for s in skills:
                normalized = s.strip().lower()
                counts[normalized] = counts.get(normalized, 0) + 1
            return counts

        recent_counts = count_skills(recent_skills)
        older_counts = count_skills(older_skills)

        all_skills = set(recent_counts.keys()) | set(older_counts.keys())
        trending_up = []
        trending_down = []
        stable = []

        for skill in all_skills:
            recent = recent_counts.get(skill, 0)
            older = older_counts.get(skill, 0)

            if older == 0 and recent > 0:
                change = 100.0
            elif older > 0:
                change = ((recent - older) / older) * 100
            else:
                change = 0.0

            current_demand = recent

            item = SkillTrendItem(
                skill=skill,
                direction="up" if change > 10 else ("down" if change < -10 else "stable"),
                change_percentage=round(change, 1),
                current_demand=current_demand,
            )

            if change > 10:
                trending_up.append(item)
            elif change < -10:
                trending_down.append(item)
            else:
                stable.append(item)

        trending_up.sort(key=lambda x: x.change_percentage, reverse=True)
        trending_down.sort(key=lambda x: x.change_percentage)

        result = SkillTrendsResponse(
            trending_up=trending_up[:10],
            trending_down=trending_down[:10],
            stable=stable[:10],
        )

        await self._set_cached(cache_key, result.model_dump())
        return result
