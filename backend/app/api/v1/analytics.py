from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    DashboardSummaryResponse,
    WeeklyPerformanceResponse,
    ApplicationFunnelResponse,
    JobMarketResponse,
    SkillCoverageResponse,
    SkillTrendsResponse,
    ResumePerformanceResponse,
    AnalyticsSnapshotResponse,
    SnapshotListResponse,
    CreateSnapshotRequest,
)
from app.services.analytics.dashboard import DashboardAnalytics
from app.services.analytics.job_market import JobMarketAnalytics
from app.services.analytics.skill_analytics import SkillAnalytics
from app.services.analytics.resume_analytics import ResumeAnalytics
from app.services.analytics.snapshot import SnapshotService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    analytics = DashboardAnalytics(db)
    return await analytics.get_dashboard_summary(user_id=current_user.id)


@router.get("/weekly", response_model=WeeklyPerformanceResponse)
async def get_weekly_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyPerformanceResponse:
    analytics = DashboardAnalytics(db)
    return await analytics.get_weekly_performance(user_id=current_user.id)


@router.get("/funnel", response_model=ApplicationFunnelResponse)
async def get_application_funnel(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationFunnelResponse:
    analytics = DashboardAnalytics(db)
    return await analytics.get_application_funnel(user_id=current_user.id)


@router.get("/skills-demand", response_model=List[dict])
async def get_skills_demand(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    analytics = JobMarketAnalytics(db)
    items = await analytics.get_skills_demand(
        user_id=current_user.id, limit=limit
    )
    return [item.model_dump() for item in items]


@router.get("/job-market", response_model=JobMarketResponse)
async def get_job_market(
    job_title: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobMarketResponse:
    analytics = JobMarketAnalytics(db)

    skills_demand = await analytics.get_skills_demand(user_id=current_user.id)
    top_job_titles = await analytics.get_top_job_titles(user_id=current_user.id)
    salary_ranges = await analytics.get_salary_ranges(
        user_id=current_user.id, job_title=job_title
    )
    companies_hiring = await analytics.get_companies_hiring(user_id=current_user.id)
    locations_demand = await analytics.get_locations_demand(user_id=current_user.id)
    remote_percentage = await analytics.get_remote_percentage(user_id=current_user.id)
    technology_trends = await analytics.get_technology_trends(user_id=current_user.id)
    industry_distribution = await analytics.get_industry_distribution(
        user_id=current_user.id
    )

    return JobMarketResponse(
        skills_demand=skills_demand,
        top_job_titles=top_job_titles,
        salary_ranges=salary_ranges,
        companies_hiring=companies_hiring,
        locations_demand=locations_demand,
        remote_percentage=remote_percentage,
        technology_trends=technology_trends,
        industry_distribution=industry_distribution,
    )


@router.get("/skill-coverage", response_model=SkillCoverageResponse)
async def get_skill_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillCoverageResponse:
    analytics = SkillAnalytics(db)
    return await analytics.get_user_skill_coverage(user_id=current_user.id)


@router.get("/skill-trends", response_model=SkillTrendsResponse)
async def get_skill_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillTrendsResponse:
    analytics = SkillAnalytics(db)
    return await analytics.get_skill_trends(user_id=current_user.id)


@router.get("/skill-recommendations", response_model=List[dict])
async def get_skill_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    analytics = SkillAnalytics(db)
    recommendations = await analytics.get_skill_recommendations(
        user_id=current_user.id
    )
    return [r.model_dump() for r in recommendations]


@router.get("/resume-performance", response_model=ResumePerformanceResponse)
async def get_resume_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumePerformanceResponse:
    analytics = ResumeAnalytics(db)
    return await analytics.get_resume_performance(user_id=current_user.id)


@router.post("/snapshot", response_model=AnalyticsSnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSnapshotResponse:
    snapshot_service = SnapshotService(db)

    if request.snapshot_type == "daily":
        snapshot = await snapshot_service.create_daily_snapshot(
            user_id=current_user.id
        )
    elif request.snapshot_type == "weekly":
        snapshot = await snapshot_service.create_weekly_snapshot(
            user_id=current_user.id
        )
    elif request.snapshot_type == "monthly":
        snapshot = await snapshot_service.create_monthly_snapshot(
            user_id=current_user.id
        )
    else:
        snapshot = await snapshot_service.create_daily_snapshot(
            user_id=current_user.id
        )

    return AnalyticsSnapshotResponse.model_validate(snapshot)


@router.get("/snapshots", response_model=SnapshotListResponse)
async def get_snapshots(
    snapshot_type: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SnapshotListResponse:
    snapshot_service = SnapshotService(db)
    snapshots = await snapshot_service.get_snapshots(
        user_id=current_user.id,
        snapshot_type=snapshot_type,
        limit=limit,
    )
    return SnapshotListResponse(
        snapshots=[
            AnalyticsSnapshotResponse.model_validate(s) for s in snapshots
        ],
        total=len(snapshots),
    )
