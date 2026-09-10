from app.services.analytics.dashboard import DashboardAnalytics
from app.services.analytics.job_market import JobMarketAnalytics
from app.services.analytics.skill_analytics import SkillAnalytics
from app.services.analytics.resume_analytics import ResumeAnalytics
from app.services.analytics.snapshot import SnapshotService

__all__ = [
    "AnalyticsService",
    "DashboardAnalytics",
    "JobMarketAnalytics",
    "SkillAnalytics",
    "ResumeAnalytics",
    "SnapshotService",
]


class AnalyticsService:
    """Comprehensive analytics for job search and applications"""

    def __init__(self, db):
        self.db = db
        self.dashboard = DashboardAnalytics(db)
        self.job_market = JobMarketAnalytics(db)
        self.skills = SkillAnalytics(db)
        self.resume = ResumeAnalytics(db)
        self.snapshot = SnapshotService(db)
