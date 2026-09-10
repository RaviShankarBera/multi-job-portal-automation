import json
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.models.application import Application, ApplicationEvent
from app.models.profile import Profile
from app.models.resume import Resume, ResumeVersion
from app.schemas.analytics import (
    DashboardSummaryResponse,
    WeeklyPerformanceResponse,
    ApplicationFunnelResponse,
    DailyPerformance,
    FunnelStage,
    ConversionRates,
    RecentActivity,
    TopSkillItem,
)


class DashboardAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _cache_key(self, user_id: int, suffix: str) -> str:
        return f"analytics:dashboard:{user_id}:{suffix}"

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

    async def _set_cached(self, key: str, data: Any, ttl: int = 300) -> None:
        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            await redis.set(key, json.dumps(data, default=str), ex=ttl)
        except Exception:
            pass

    async def get_dashboard_summary(self, user_id: int) -> DashboardSummaryResponse:
        cache_key = self._cache_key(user_id, "summary")
        cached = await self._get_cached(cache_key)
        if cached:
            return DashboardSummaryResponse(**cached)

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        jobs_total = await self.db.execute(select(func.count(Job.id)))
        jobs_found_total = jobs_total.scalar() or 0

        jobs_today_result = await self.db.execute(
            select(func.count(Job.id)).where(Job.collected_date >= today_start)
        )
        jobs_today = jobs_today_result.scalar() or 0

        jobs_week_result = await self.db.execute(
            select(func.count(Job.id)).where(Job.collected_date >= week_start)
        )
        jobs_this_week = jobs_week_result.scalar() or 0

        apps_total = await self.db.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        applications_total = apps_total.scalar() or 0

        apps_week = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= week_start,
                )
            )
        )
        applications_this_week = apps_week.scalar() or 0

        apps_month = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= month_start,
                )
            )
        )
        applications_this_month = apps_month.scalar() or 0

        status_counts = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_map = {row[0]: row[1] for row in status_counts.all()}

        interview_statuses = [
            "interview", "technical_round", "hr_round", "recruiter_contacted"
        ]
        interviews_count = sum(status_map.get(s, 0) for s in interview_statuses)
        offers_count = status_map.get("offer", 0)
        rejections_count = status_map.get("rejected", 0)
        pending_statuses = [
            "applied", "application_submitted", "hr_viewed", "on_hold"
        ]
        pending_count = sum(status_map.get(s, 0) for s in pending_statuses)

        avg_match = await self.db.execute(
            select(func.avg(JobMatch.overall_score)).where(JobMatch.user_id == user_id)
        )
        match_rate = round(avg_match.scalar() or 0.0, 2)

        conversion_rates = await self._calculate_conversion_rates(user_id)
        top_skills = await self._get_top_skills_demand(user_id, limit=5)
        recent_activity = await self._get_recent_activity(user_id, limit=5)
        recommended_jobs = await self._get_recommended_jobs(user_id, limit=5)
        application_pipeline = await self._get_application_pipeline(user_id)
        upcoming_follow_ups = await self._get_upcoming_follow_ups(user_id, limit=5)

        result = DashboardSummaryResponse(
            jobs_found_total=jobs_found_total,
            jobs_today=jobs_today,
            jobs_this_week=jobs_this_week,
            applications_total=applications_total,
            applications_this_week=applications_this_week,
            applications_this_month=applications_this_month,
            interviews_count=interviews_count,
            offers_count=offers_count,
            rejections_count=rejections_count,
            pending_count=pending_count,
            match_rate=match_rate,
            conversion_rates=conversion_rates,
            top_skills_demand=top_skills,
            recent_activity=recent_activity,
            recommended_jobs=recommended_jobs,
            application_pipeline=application_pipeline,
            upcoming_follow_ups=upcoming_follow_ups,
        )

        await self._set_cached(cache_key, result.model_dump(), ttl=300)
        return result

    async def _calculate_conversion_rates(self, user_id: int) -> ConversionRates:
        total_applied = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["applied", "application_submitted"]),
                )
            )
        )
        applied_count = total_applied.scalar() or 0

        hr_viewed = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_([
                        "hr_viewed", "recruiter_contacted", "interview",
                        "technical_round", "hr_round", "offer"
                    ]),
                )
            )
        )
        hr_count = hr_viewed.scalar() or 0

        interview_count_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_([
                        "interview", "technical_round", "hr_round", "offer"
                    ]),
                )
            )
        )
        interview_count = interview_count_result.scalar() or 0

        offer_count_result = await self.db.execute(
            select(func.count(Application.id)).where(
                and_(
                    Application.user_id == user_id,
                    Application.status == "offer",
                )
            )
        )
        offer_count = offer_count_result.scalar() or 0

        app_to_hr = (hr_count / applied_count * 100) if applied_count > 0 else 0.0
        hr_to_int = (interview_count / hr_count * 100) if hr_count > 0 else 0.0
        int_to_offer = (offer_count / interview_count * 100) if interview_count > 0 else 0.0

        return ConversionRates(
            application_to_hr=round(app_to_hr, 1),
            hr_to_interview=round(hr_to_int, 1),
            interview_to_offer=round(int_to_offer, 1),
        )

    async def _get_top_skills_demand(
        self, user_id: int, limit: int = 5
    ) -> List[TopSkillItem]:
        result = await self.db.execute(
            select(Job.required_skills).where(
                Job.id.in_(
                    select(SavedJob.job_id).where(SavedJob.user_id == user_id)
                )
            )
        )
        all_skills = []
        for row in result.scalars().all():
            if row:
                all_skills.extend(row)

        if not all_skills:
            result_all = await self.db.execute(select(Job.required_skills))
            for row in result_all.scalars().all():
                if row:
                    all_skills.extend(row)

        skill_counts: Dict[str, int] = {}
        for skill in all_skills:
            normalized = skill.strip().lower()
            skill_counts[normalized] = skill_counts.get(normalized, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        total = sum(skill_counts.values()) if skill_counts else 1

        return [
            TopSkillItem(
                skill=skill,
                count=count,
                percentage=round(count / total * 100, 1),
            )
            for skill, count in sorted_skills
        ]

    async def _get_recent_activity(
        self, user_id: int, limit: int = 5
    ) -> List[RecentActivity]:
        result = await self.db.execute(
            select(ApplicationEvent)
            .join(Application, ApplicationEvent.application_id == Application.id)
            .where(Application.user_id == user_id)
            .order_by(ApplicationEvent.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()

        return [
            RecentActivity(
                type=event.event_type,
                description=event.description or f"Event: {event.event_type}",
                timestamp=event.created_at,
            )
            for event in events
        ]

    async def _get_recommended_jobs(
        self, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Job, JobMatch.overall_score)
            .join(JobMatch, Job.id == JobMatch.job_id)
            .where(JobMatch.user_id == user_id)
            .order_by(JobMatch.overall_score.desc())
            .limit(limit)
        )
        rows = result.all()

        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "match_score": round(score, 1),
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
            }
            for job, score in rows
        ]

    async def _get_application_pipeline(self, user_id: int) -> Dict[str, int]:
        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _get_upcoming_follow_ups(
        self, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Application)
            .join(Job, Application.job_id == Job.id)
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.next_follow_up.isnot(None),
                    Application.next_follow_up >= now,
                    Application.status.notin_(["rejected", "withdrawn"]),
                )
            )
            .order_by(Application.next_follow_up.asc())
            .limit(limit)
        )
        apps = result.scalars().all()

        return [
            {
                "application_id": app.id,
                "job_title": app.job.title,
                "company": app.job.company,
                "follow_up_date": app.next_follow_up.isoformat() if app.next_follow_up else None,
                "status": app.status,
            }
            for app in apps
        ]

    async def get_weekly_performance(self, user_id: int) -> WeeklyPerformanceResponse:
        cache_key = self._cache_key(user_id, "weekly")
        cached = await self._get_cached(cache_key)
        if cached:
            return WeeklyPerformanceResponse(**cached)

        now = datetime.utcnow()
        week_end = now.date()
        week_start = (now - timedelta(days=6)).date()

        daily_data = []
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            apps_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    and_(
                        Application.user_id == user_id,
                        Application.created_at >= day_start,
                        Application.created_at < day_end,
                    )
                )
            )
            apps_count = apps_result.scalar() or 0

            responses_result = await self.db.execute(
                select(func.count(ApplicationEvent.id))
                .join(Application, ApplicationEvent.application_id == Application.id)
                .where(
                    and_(
                        Application.user_id == user_id,
                        ApplicationEvent.event_type == "status_change",
                        ApplicationEvent.created_at >= day_start,
                        ApplicationEvent.created_at < day_end,
                    )
                )
            )
            responses_count = responses_result.scalar() or 0

            interviews_result = await self.db.execute(
                select(func.count(Application.id)).where(
                    and_(
                        Application.user_id == user_id,
                        Application.status.in_([
                            "interview", "technical_round", "hr_round"
                        ]),
                        Application.updated_at >= day_start,
                        Application.updated_at < day_end,
                    )
                )
            )
            interviews_count = interviews_result.scalar() or 0

            daily_data.append(
                DailyPerformance(
                    date=current_date.isoformat(),
                    applications=apps_count,
                    responses=responses_count,
                    interviews=interviews_count,
                )
            )

        result = WeeklyPerformanceResponse(
            period_start=week_start.isoformat(),
            period_end=week_end.isoformat(),
            daily_data=daily_data,
            total_applications=sum(d.applications for d in daily_data),
            total_responses=sum(d.responses for d in daily_data),
            total_interviews=sum(d.interviews for d in daily_data),
        )

        await self._set_cached(cache_key, result.model_dump(), ttl=600)
        return result

    async def get_application_funnel(self, user_id: int) -> ApplicationFunnelResponse:
        cache_key = self._cache_key(user_id, "funnel")
        cached = await self._get_cached(cache_key)
        if cached:
            return ApplicationFunnelResponse(**cached)

        stage_mapping = {
            "saved": "saved",
            "interested": "saved",
            "resume_tailored": "saved",
            "ready_to_apply": "saved",
            "applied": "applied",
            "application_submitted": "applied",
            "hr_viewed": "screening",
            "recruiter_contacted": "screening",
            "interview": "interview",
            "technical_round": "interview",
            "hr_round": "interview",
            "offer": "offer",
            "rejected": "rejected",
            "withdrawn": "withdrawn",
            "on_hold": "screening",
        }

        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}

        stage_counts: Dict[str, int] = {
            "saved": 0,
            "applied": 0,
            "screening": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
            "withdrawn": 0,
        }

        for status, count in status_counts.items():
            stage = stage_mapping.get(status, "saved")
            stage_counts[stage] = stage_counts.get(stage, 0) + count

        total = sum(status_counts.values())

        ordered_stages = ["saved", "applied", "screening", "interview", "offer"]
        stages = []
        for stage_name in ordered_stages:
            count = stage_counts.get(stage_name, 0)
            percentage = (count / total * 100) if total > 0 else 0.0
            stages.append(
                FunnelStage(
                    stage=stage_name,
                    count=count,
                    percentage=round(percentage, 1),
                )
            )

        conversion_rates = {}
        for i in range(len(ordered_stages) - 1):
            from_stage = ordered_stages[i]
            to_stage = ordered_stages[i + 1]
            from_count = stage_counts.get(from_stage, 0)
            to_count = stage_counts.get(to_stage, 0)
            rate = (to_count / from_count * 100) if from_count > 0 else 0.0
            conversion_rates[f"{from_stage}_to_{to_stage}"] = round(rate, 1)

        result_resp = ApplicationFunnelResponse(
            stages=stages,
            total=total,
            conversion_rates=conversion_rates,
        )

        await self._set_cached(cache_key, result_resp.model_dump(), ttl=300)
        return result_resp
