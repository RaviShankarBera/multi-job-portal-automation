from datetime import datetime, date, timedelta
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsSnapshot
from app.services.analytics.dashboard import DashboardAnalytics
from app.services.analytics.job_market import JobMarketAnalytics
from app.services.analytics.skill_analytics import SkillAnalytics
from app.services.analytics.resume_analytics import ResumeAnalytics


class SnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dashboard = DashboardAnalytics(db)
        self.job_market = JobMarketAnalytics(db)
        self.skills = SkillAnalytics(db)
        self.resume = ResumeAnalytics(db)

    async def create_daily_snapshot(self, user_id: int) -> AnalyticsSnapshot:
        today = date.today()

        existing = await self.db.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.user_id == user_id,
                    AnalyticsSnapshot.snapshot_type == "daily",
                    AnalyticsSnapshot.snapshot_date == today,
                )
            )
        )
        if existing.scalar_one_or_none():
            return await self._update_snapshot(user_id, "daily", today)

        dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
        weekly_data = await self.dashboard.get_weekly_performance(user_id)
        funnel_data = await self.dashboard.get_application_funnel(user_id)

        snapshot_data = {
            "dashboard": dashboard_data.model_dump(),
            "weekly_performance": weekly_data.model_dump(),
            "funnel": funnel_data.model_dump(),
        }

        snapshot = AnalyticsSnapshot(
            user_id=user_id,
            snapshot_type="daily",
            snapshot_date=today,
            data=snapshot_data,
        )
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def create_weekly_snapshot(self, user_id: int) -> AnalyticsSnapshot:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        existing = await self.db.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.user_id == user_id,
                    AnalyticsSnapshot.snapshot_type == "weekly",
                    AnalyticsSnapshot.snapshot_date == week_start,
                )
            )
        )
        if existing.scalar_one_or_none():
            return await self._update_snapshot(user_id, "weekly", week_start)

        dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
        weekly_data = await self.dashboard.get_weekly_performance(user_id)
        funnel_data = await self.dashboard.get_application_funnel(user_id)
        market_data = await self.job_market.get_skills_demand(user_id, limit=10)
        skill_coverage = await self.skills.get_user_skill_coverage(user_id)

        snapshot_data = {
            "dashboard": dashboard_data.model_dump(),
            "weekly_performance": weekly_data.model_dump(),
            "funnel": funnel_data.model_dump(),
            "top_skills": [s.model_dump() for s in market_data],
            "skill_coverage": skill_coverage.model_dump(),
        }

        snapshot = AnalyticsSnapshot(
            user_id=user_id,
            snapshot_type="weekly",
            snapshot_date=week_start,
            data=snapshot_data,
        )
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def create_monthly_snapshot(self, user_id: int) -> AnalyticsSnapshot:
        today = date.today()
        month_start = today.replace(day=1)

        existing = await self.db.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.user_id == user_id,
                    AnalyticsSnapshot.snapshot_type == "monthly",
                    AnalyticsSnapshot.snapshot_date == month_start,
                )
            )
        )
        if existing.scalar_one_or_none():
            return await self._update_snapshot(user_id, "monthly", month_start)

        dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
        weekly_data = await self.dashboard.get_weekly_performance(user_id)
        funnel_data = await self.dashboard.get_application_funnel(user_id)
        market_data = await self.job_market.get_skills_demand(user_id, limit=15)
        skill_coverage = await self.skills.get_user_skill_coverage(user_id)
        skill_recommendations = await self.skills.get_skill_recommendations(user_id)
        resume_performance = await self.resume.get_resume_performance(user_id)

        snapshot_data = {
            "dashboard": dashboard_data.model_dump(),
            "weekly_performance": weekly_data.model_dump(),
            "funnel": funnel_data.model_dump(),
            "top_skills": [s.model_dump() for s in market_data],
            "skill_coverage": skill_coverage.model_dump(),
            "skill_recommendations": [r.model_dump() for r in skill_recommendations],
            "resume_performance": resume_performance.model_dump(),
        }

        snapshot = AnalyticsSnapshot(
            user_id=user_id,
            snapshot_type="monthly",
            snapshot_date=month_start,
            data=snapshot_data,
        )
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def _update_snapshot(
        self, user_id: int, snapshot_type: str, snapshot_date: date
    ) -> AnalyticsSnapshot:
        result = await self.db.execute(
            select(AnalyticsSnapshot).where(
                and_(
                    AnalyticsSnapshot.user_id == user_id,
                    AnalyticsSnapshot.snapshot_type == snapshot_type,
                    AnalyticsSnapshot.snapshot_date == snapshot_date,
                )
            )
        )
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            raise ValueError("Snapshot not found for update")

        if snapshot_type == "daily":
            dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
            weekly_data = await self.dashboard.get_weekly_performance(user_id)
            funnel_data = await self.dashboard.get_application_funnel(user_id)
            snapshot.data = {
                "dashboard": dashboard_data.model_dump(),
                "weekly_performance": weekly_data.model_dump(),
                "funnel": funnel_data.model_dump(),
            }
        elif snapshot_type == "weekly":
            dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
            weekly_data = await self.dashboard.get_weekly_performance(user_id)
            funnel_data = await self.dashboard.get_application_funnel(user_id)
            market_data = await self.job_market.get_skills_demand(user_id, limit=10)
            skill_coverage = await self.skills.get_user_skill_coverage(user_id)
            snapshot.data = {
                "dashboard": dashboard_data.model_dump(),
                "weekly_performance": weekly_data.model_dump(),
                "funnel": funnel_data.model_dump(),
                "top_skills": [s.model_dump() for s in market_data],
                "skill_coverage": skill_coverage.model_dump(),
            }
        elif snapshot_type == "monthly":
            dashboard_data = await self.dashboard.get_dashboard_summary(user_id)
            weekly_data = await self.dashboard.get_weekly_performance(user_id)
            funnel_data = await self.dashboard.get_application_funnel(user_id)
            market_data = await self.job_market.get_skills_demand(user_id, limit=15)
            skill_coverage = await self.skills.get_user_skill_coverage(user_id)
            skill_recommendations = await self.skills.get_skill_recommendations(user_id)
            resume_performance = await self.resume.get_resume_performance(user_id)
            snapshot.data = {
                "dashboard": dashboard_data.model_dump(),
                "weekly_performance": weekly_data.model_dump(),
                "funnel": funnel_data.model_dump(),
                "top_skills": [s.model_dump() for s in market_data],
                "skill_coverage": skill_coverage.model_dump(),
                "skill_recommendations": [
                    r.model_dump() for r in skill_recommendations
                ],
                "resume_performance": resume_performance.model_dump(),
            }

        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_snapshots(
        self,
        user_id: int,
        snapshot_type: Optional[str] = None,
        limit: int = 30,
    ) -> List[AnalyticsSnapshot]:
        query = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.user_id == user_id
        )

        if snapshot_type:
            query = query.where(AnalyticsSnapshot.snapshot_type == snapshot_type)

        query = query.order_by(AnalyticsSnapshot.snapshot_date.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
