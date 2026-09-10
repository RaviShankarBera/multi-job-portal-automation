import json
import statistics
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.models.application import Application
from app.schemas.analytics import (
    JobMarketResponse,
    TopSkillItem,
    SalaryStats,
)


class JobMarketAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _cache_key(self, user_id: int, suffix: str) -> str:
        return f"analytics:market:{user_id}:{suffix}"

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

    async def get_skills_demand(
        self, user_id: int, limit: int = 20
    ) -> List[TopSkillItem]:
        cache_key = self._cache_key(user_id, f"skills_{limit}")
        cached = await self._get_cached(cache_key)
        if cached:
            return [TopSkillItem(**item) for item in cached]

        result = await self.db.execute(select(Job.required_skills))
        all_skills: List[str] = []
        for row in result.scalars().all():
            if row:
                all_skills.extend(row)

        skill_counts: Dict[str, int] = {}
        for skill in all_skills:
            normalized = skill.strip().lower()
            skill_counts[normalized] = skill_counts.get(normalized, 0) + 1

        sorted_skills = sorted(
            skill_counts.items(), key=lambda x: x[1], reverse=True
        )[:limit]
        total = sum(skill_counts.values()) if skill_counts else 1

        items = [
            TopSkillItem(
                skill=skill,
                count=count,
                percentage=round(count / total * 100, 1),
            )
            for skill, count in sorted_skills
        ]

        await self._set_cached(cache_key, [item.model_dump() for item in items])
        return items

    async def get_top_job_titles(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(user_id, f"titles_{limit}")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(Job.title, func.count(Job.id).label("count"))
            .group_by(Job.title)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
        )
        titles = [{"title": row[0], "count": row[1]} for row in result.all()]

        await self._set_cached(cache_key, titles)
        return titles

    async def get_salary_ranges(
        self, user_id: int, job_title: Optional[str] = None
    ) -> SalaryStats:
        cache_key = self._cache_key(
            user_id, f"salary_{job_title or 'all'}"
        )
        cached = await self._get_cached(cache_key)
        if cached:
            return SalaryStats(**cached)

        query = select(Job.salary_min, Job.salary_max).where(
            and_(Job.salary_min.isnot(None), Job.salary_max.isnot(None))
        )
        if job_title:
            query = query.where(Job.title.ilike(f"%{job_title}%"))

        result = await self.db.execute(query)
        salary_pairs = result.all()

        min_salaries = [row[0] for row in salary_pairs if row[0] is not None]
        max_salaries = [row[1] for row in salary_pairs if row[1] is not None]
        all_salaries = min_salaries + max_salaries

        if not all_salaries:
            stats = SalaryStats(sample_size=0)
        else:
            all_salaries_sorted = sorted(all_salaries)
            median_idx = len(all_salaries_sorted) // 2
            median_val = (
                all_salaries_sorted[median_idx]
                if len(all_salaries_sorted) % 2 == 1
                else (
                    all_salaries_sorted[median_idx - 1]
                    + all_salaries_sorted[median_idx]
                ) / 2
            )
            stats = SalaryStats(
                min_salary=min(all_salaries),
                max_salary=max(all_salaries),
                avg_salary=round(statistics.mean(all_salaries), 2),
                median_salary=round(median_val, 2),
                sample_size=len(salary_pairs),
            )

        await self._set_cached(cache_key, stats.model_dump())
        return stats

    async def get_companies_hiring(
        self, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(user_id, f"companies_{limit}")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(Job.company, func.count(Job.id).label("count"))
            .group_by(Job.company)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
        )
        companies = [{"company": row[0], "job_count": row[1]} for row in result.all()]

        await self._set_cached(cache_key, companies)
        return companies

    async def get_locations_demand(self, user_id: int) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(user_id, "locations")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(Job.location, func.count(Job.id).label("count"))
            .group_by(Job.location)
            .order_by(func.count(Job.id).desc())
            .limit(20)
        )
        locations = [{"location": row[0], "count": row[1]} for row in result.all()]

        await self._set_cached(cache_key, locations)
        return locations

    async def get_remote_percentage(self, user_id: int) -> float:
        cache_key = self._cache_key(user_id, "remote_pct")
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        total_result = await self.db.execute(select(func.count(Job.id)))
        total = total_result.scalar() or 0

        if total == 0:
            return 0.0

        remote_result = await self.db.execute(
            select(func.count(Job.id)).where(
                Job.remote_status.in_(["remote", "fully_remote"])
            )
        )
        remote_count = remote_result.scalar() or 0

        percentage = round(remote_count / total * 100, 1)
        await self._set_cached(cache_key, percentage)
        return percentage

    async def get_technology_trends(self, user_id: int) -> Dict[str, Any]:
        cache_key = self._cache_key(user_id, "tech_trends")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        now = datetime.utcnow()
        recent_cutoff = now - timedelta(days=30)
        older_cutoff = now - timedelta(days=90)

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

        all_skills_set = set(recent_counts.keys()) | set(older_counts.keys())
        trending_up = []
        trending_down = []
        stable = []

        for skill in all_skills_set:
            recent = recent_counts.get(skill, 0)
            older = older_counts.get(skill, 0)

            if older == 0 and recent > 0:
                change = 100.0
            elif older > 0:
                change = ((recent - older) / older) * 100
            else:
                change = 0.0

            if change > 10:
                trending_up.append({
                    "skill": skill,
                    "change_percentage": round(change, 1),
                    "recent_count": recent,
                    "older_count": older,
                })
            elif change < -10:
                trending_down.append({
                    "skill": skill,
                    "change_percentage": round(change, 1),
                    "recent_count": recent,
                    "older_count": older,
                })
            else:
                stable.append({
                    "skill": skill,
                    "change_percentage": round(change, 1),
                    "recent_count": recent,
                    "older_count": older,
                })

        trending_up.sort(key=lambda x: x["change_percentage"], reverse=True)
        trending_down.sort(key=lambda x: x["change_percentage"])

        result = {
            "trending_up": trending_up[:10],
            "trending_down": trending_down[:10],
            "stable_count": len(stable),
            "analysis_period_days": 30,
        }

        await self._set_cached(cache_key, result)
        return result

    async def get_industry_distribution(self, user_id: int) -> List[Dict[str, Any]]:
        cache_key = self._cache_key(user_id, "industries")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        result = await self.db.execute(
            select(
                Job.employment_type,
                func.count(Job.id).label("count"),
            )
            .group_by(Job.employment_type)
            .order_by(func.count(Job.id).desc())
        )
        distribution = [
            {"industry": row[0], "count": row[1]} for row in result.all()
        ]

        await self._set_cached(cache_key, distribution)
        return distribution
