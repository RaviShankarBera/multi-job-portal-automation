import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeVersion
from app.models.application import Application
from app.schemas.analytics import (
    ResumePerformanceResponse,
    ATSStats,
    ResumePerformanceItem,
)


class ResumeAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _cache_key(self, user_id: int, suffix: str) -> str:
        return f"analytics:resume:{user_id}:{suffix}"

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

    async def get_ats_scores(self, user_id: int) -> ATSStats:
        cache_key = self._cache_key(user_id, "ats_scores")
        cached = await self._get_cached(cache_key)
        if cached:
            return ATSStats(**cached)

        result = await self.db.execute(
            select(ResumeVersion.ats_score)
            .join(Resume, ResumeVersion.resume_id == Resume.id)
            .where(
                and_(
                    Resume.user_id == user_id,
                    ResumeVersion.ats_score.isnot(None),
                )
            )
        )
        scores = [row[0] for row in result.all()]

        if not scores:
            stats = ATSStats()
        else:
            scores_sorted = sorted(scores)
            median_idx = len(scores_sorted) // 2
            stats = ATSStats(
                average_score=round(sum(scores) / len(scores), 2),
                min_score=min(scores),
                max_score=max(scores),
                total_resumes=len(scores),
                scores_over_time=[],
            )

        await self._set_cached(cache_key, stats.model_dump())
        return stats

    async def get_resume_performance(self, user_id: int) -> ResumePerformanceResponse:
        cache_key = self._cache_key(user_id, "performance")
        cached = await self._get_cached(cache_key)
        if cached:
            return ResumePerformanceResponse(**cached)

        resumes_result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        resumes = resumes_result.scalars().all()

        ats_stats = await self.get_ats_scores(user_id)

        resume_performance = []
        for resume in resumes:
            versions_result = await self.db.execute(
                select(func.count(ResumeVersion.id)).where(
                    ResumeVersion.resume_id == resume.id
                )
            )
            version_count = versions_result.scalar() or 0

            avg_ats_result = await self.db.execute(
                select(func.avg(ResumeVersion.ats_score)).where(
                    and_(
                        ResumeVersion.resume_id == resume.id,
                        ResumeVersion.ats_score.isnot(None),
                    )
                )
            )
            avg_ats = avg_ats_result.scalar()

            apps_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    Application.resume_id == resume.id
                )
            )
            apps_count = apps_result.scalar() or 0

            interview_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    and_(
                        Application.resume_id == resume.id,
                        Application.status.in_([
                            "interview", "technical_round", "hr_round", "offer"
                        ]),
                    )
                )
            )
            interview_count = interview_result.scalar() or 0

            interview_rate = (
                (interview_count / apps_count * 100) if apps_count > 0 else 0.0
            )

            resume_performance.append(
                ResumePerformanceItem(
                    resume_id=resume.id,
                    title=resume.title,
                    version_count=version_count,
                    average_ats_score=round(avg_ats, 2) if avg_ats else 0.0,
                    applications_count=apps_count,
                    interview_rate=round(interview_rate, 1),
                )
            )

        correlation_insight = self._generate_correlation_insight(resume_performance)

        result = ResumePerformanceResponse(
            ats_scores=ats_stats,
            resume_performance=resume_performance,
            correlation_insight=correlation_insight,
        )

        await self._set_cached(cache_key, result.model_dump())
        return result

    def _generate_correlation_insight(
        self, performances: List[ResumePerformanceItem]
    ) -> str:
        if not performances:
            return "No resume data available for analysis."

        scored = [p for p in performances if p.average_ats_score > 0]
        if len(scored) < 2:
            return "Insufficient data for correlation analysis. Add more resume versions."

        best_ats = max(scored, key=lambda x: x.average_ats_score)
        worst_ats = min(scored, key=lambda x: x.average_ats_score)

        best_interview = max(scored, key=lambda x: x.interview_rate)
        worst_interview = min(scored, key=lambda x: x.interview_rate)

        if best_ats.resume_id == best_interview.resume_id:
            return (
                f"Resume '{best_ats.title}' has the highest ATS score "
                f"({best_ats.average_ats_score}) and best interview rate "
                f"({best_ats.interview_rate}%). Higher ATS scores correlate "
                f"with better outcomes."
            )

        if best_ats.average_ats_score > 70 and best_ats.interview_rate < 20:
            return (
                f"Resume '{best_ats.title}' has a high ATS score "
                f"({best_ats.average_ats_score}) but lower interview rate "
                f"({best_ats.interview_rate}%). Consider tailoring content "
                f"for human reviewers."
            )

        return (
            f"Resume '{best_interview.title}' achieves the best interview rate "
            f"({best_interview.interview_rate}%). Focus on what makes this "
            f"resume effective for future applications."
        )
