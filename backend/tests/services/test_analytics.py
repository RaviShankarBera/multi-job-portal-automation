import pytest
import pytest_asyncio
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.models.application import Application, ApplicationEvent
from app.models.profile import Profile
from app.models.resume import Resume, ResumeVersion
from app.schemas.job import JobCreate
from app.services.analytics.dashboard import DashboardAnalytics
from app.services.analytics.job_market import JobMarketAnalytics
from app.services.analytics.skill_analytics import SkillAnalytics
from app.services.analytics.resume_analytics import ResumeAnalytics
from app.services.analytics.snapshot import SnapshotService


async def _create_test_job(
    db: AsyncSession,
    title: str = "Software Engineer",
    company: str = "Test Corp",
    location: str = "Test City",
    required_skills: list = None,
    salary_min: float = 100000,
    salary_max: float = 150000,
    remote_status: str = "remote",
) -> Job:
    from app.services.job import JobService

    service = JobService(db)
    data = JobCreate(
        title=title,
        company=company,
        location=location,
        required_skills=required_skills or ["Python", "FastAPI"],
        salary_min=salary_min,
        salary_max=salary_max,
        remote_status=remote_status,
    )
    return await service.create_job(data)


async def _create_test_profile(
    db: AsyncSession,
    user_id: int,
    skills: list = None,
) -> Profile:
    profile = Profile(
        user_id=user_id,
        name="Test User",
        skills=skills or ["Python", "FastAPI", "SQL"],
        technical_skills=["Python", "FastAPI", "SQL"],
        target_title="Senior Software Engineer",
        years_of_experience=5,
        expected_salary=130000,
        location="Test City",
        remote_preference="remote",
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def _create_test_application(
    db: AsyncSession,
    user_id: int,
    job_id: int,
    status: str = "saved",
    resume_id: int = None,
) -> Application:
    application = Application(
        user_id=user_id,
        job_id=job_id,
        status=status,
        resume_id=resume_id,
        source="manual",
    )
    db.add(application)
    await db.flush()
    await db.refresh(application)
    return application


@pytest.mark.asyncio
async def test_dashboard_summary_empty(db_session: AsyncSession):
    analytics = DashboardAnalytics(db_session)
    summary = await analytics.get_dashboard_summary(user_id=9999)

    assert summary.jobs_found_total == 0
    assert summary.applications_total == 0
    assert summary.interviews_count == 0
    assert summary.offers_count == 0
    assert summary.match_rate == 0.0
    assert summary.top_skills_demand == []
    assert summary.recent_activity == []


@pytest.mark.asyncio
async def test_dashboard_summary_with_data(db_session: AsyncSession):
    job1 = await _create_test_job(
        db_session, title="Job 1", required_skills=["Python", "FastAPI"]
    )
    job2 = await _create_test_job(
        db_session, title="Job 2", required_skills=["Java", "Spring"]
    )

    await _create_test_application(
        db_session, user_id=1, job_id=job1.id, status="applied"
    )
    await _create_test_application(
        db_session, user_id=1, job_id=job2.id, status="interview"
    )

    analytics = DashboardAnalytics(db_session)
    summary = await analytics.get_dashboard_summary(user_id=1)

    assert summary.jobs_found_total >= 2
    assert summary.applications_total >= 2
    assert summary.interviews_count >= 1


@pytest.mark.asyncio
async def test_weekly_performance(db_session: AsyncSession):
    job = await _create_test_job(db_session)
    await _create_test_application(
        db_session, user_id=1, job_id=job.id, status="applied"
    )

    analytics = DashboardAnalytics(db_session)
    performance = await analytics.get_weekly_performance(user_id=1)

    assert performance.period_start is not None
    assert performance.period_end is not None
    assert len(performance.daily_data) == 7
    assert performance.total_applications >= 0


@pytest.mark.asyncio
async def test_application_funnel(db_session: AsyncSession):
    job1 = await _create_test_job(db_session, title="Funnel Job 1")
    job2 = await _create_test_job(db_session, title="Funnel Job 2")
    job3 = await _create_test_job(db_session, title="Funnel Job 3")

    await _create_test_application(
        db_session, user_id=1, job_id=job1.id, status="saved"
    )
    await _create_test_application(
        db_session, user_id=1, job_id=job2.id, status="applied"
    )
    await _create_test_application(
        db_session, user_id=1, job_id=job3.id, status="interview"
    )

    analytics = DashboardAnalytics(db_session)
    funnel = await analytics.get_application_funnel(user_id=1)

    assert funnel.total >= 3
    assert len(funnel.stages) > 0


@pytest.mark.asyncio
async def test_skills_demand(db_session: AsyncSession):
    await _create_test_job(
        db_session, title="Py Job", required_skills=["Python", "FastAPI"]
    )
    await _create_test_job(
        db_session, title="Py Job 2", required_skills=["Python", "Django"]
    )
    await _create_test_job(
        db_session, title="Java Job", required_skills=["Java", "Spring"]
    )

    analytics = JobMarketAnalytics(db_session)
    skills = await analytics.get_skills_demand(user_id=1, limit=5)

    assert len(skills) > 0
    assert skills[0].skill is not None
    assert skills[0].count > 0


@pytest.mark.asyncio
async def test_top_job_titles(db_session: AsyncSession):
    await _create_test_job(db_session, title="Python Developer")
    await _create_test_job(db_session, title="Python Developer")
    await _create_test_job(db_session, title="Java Developer")

    analytics = JobMarketAnalytics(db_session)
    titles = await analytics.get_top_job_titles(user_id=1, limit=5)

    assert len(titles) > 0
    assert titles[0]["count"] >= 2


@pytest.mark.asyncio
async def test_salary_ranges(db_session: AsyncSession):
    await _create_test_job(
        db_session, salary_min=100000, salary_max=150000
    )
    await _create_test_job(
        db_session, salary_min=120000, salary_max=180000
    )

    analytics = JobMarketAnalytics(db_session)
    salary = await analytics.get_salary_ranges(user_id=1)

    assert salary.min_salary is not None
    assert salary.max_salary is not None
    assert salary.avg_salary is not None
    assert salary.sample_size >= 2


@pytest.mark.asyncio
async def test_companies_hiring(db_session: AsyncSession):
    await _create_test_job(db_session, company="Company A")
    await _create_test_job(db_session, company="Company A")
    await _create_test_job(db_session, company="Company B")

    analytics = JobMarketAnalytics(db_session)
    companies = await analytics.get_companies_hiring(user_id=1, limit=5)

    assert len(companies) > 0
    assert companies[0]["job_count"] >= 2


@pytest.mark.asyncio
async def test_locations_demand(db_session: AsyncSession):
    await _create_test_job(db_session, location="New York, NY")
    await _create_test_job(db_session, location="San Francisco, CA")

    analytics = JobMarketAnalytics(db_session)
    locations = await analytics.get_locations_demand(user_id=1)

    assert len(locations) > 0


@pytest.mark.asyncio
async def test_remote_percentage(db_session: AsyncSession):
    await _create_test_job(db_session, remote_status="remote")
    await _create_test_job(db_session, remote_status="remote")
    await _create_test_job(db_session, remote_status="onsite")

    analytics = JobMarketAnalytics(db_session)
    percentage = await analytics.get_remote_percentage(user_id=1)

    assert 0 <= percentage <= 100


@pytest.mark.asyncio
async def test_technology_trends(db_session: AsyncSession):
    await _create_test_job(
        db_session, title="Trend Job", required_skills=["Python", "FastAPI"]
    )

    analytics = JobMarketAnalytics(db_session)
    trends = await analytics.get_technology_trends(user_id=1)

    assert "trending_up" in trends
    assert "trending_down" in trends


@pytest.mark.asyncio
async def test_user_skill_coverage(db_session: AsyncSession):
    await _create_test_profile(db_session, user_id=1, skills=["Python", "FastAPI"])
    await _create_test_job(
        db_session, required_skills=["Python", "FastAPI", "Docker", "K8s"]
    )

    analytics = SkillAnalytics(db_session)
    coverage = await analytics.get_user_skill_coverage(user_id=1)

    assert coverage.total_market_skills > 0
    assert coverage.coverage_percentage >= 0


@pytest.mark.asyncio
async def test_skill_recommendations(db_session: AsyncSession):
    await _create_test_profile(db_session, user_id=1, skills=["Python"])
    await _create_test_job(
        db_session, required_skills=["Python", "FastAPI", "Docker"]
    )
    await _create_test_job(
        db_session, required_skills=["Python", "FastAPI", "K8s"]
    )

    analytics = SkillAnalytics(db_session)
    recommendations = await analytics.get_skill_recommendations(user_id=1)

    assert isinstance(recommendations, list)


@pytest.mark.asyncio
async def test_skill_trends(db_session: AsyncSession):
    await _create_test_job(
        db_session, required_skills=["Python", "FastAPI"]
    )

    analytics = SkillAnalytics(db_session)
    trends = await analytics.get_skill_trends(user_id=1)

    assert isinstance(trends.trending_up, list)
    assert isinstance(trends.trending_down, list)


@pytest.mark.asyncio
async def test_resume_performance(db_session: AsyncSession):
    resume = Resume(
        user_id=1,
        title="Test Resume",
        original_filename="test.pdf",
        file_path="/tmp/test.pdf",
        file_size=1024,
        file_type="pdf",
    )
    db_session.add(resume)
    await db_session.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        ats_score=75.0,
    )
    db_session.add(version)
    await db_session.flush()

    analytics = ResumeAnalytics(db_session)
    performance = await analytics.get_resume_performance(user_id=1)

    assert len(performance.resume_performance) >= 1
    assert performance.ats_scores.total_resumes >= 1


@pytest.mark.asyncio
async def test_create_daily_snapshot(db_session: AsyncSession):
    snapshot_service = SnapshotService(db_session)
    snapshot = await snapshot_service.create_daily_snapshot(user_id=1)

    assert snapshot.id is not None
    assert snapshot.snapshot_type == "daily"
    assert snapshot.snapshot_date == date.today()
    assert snapshot.data is not None


@pytest.mark.asyncio
async def test_create_weekly_snapshot(db_session: AsyncSession):
    snapshot_service = SnapshotService(db_session)
    snapshot = await snapshot_service.create_weekly_snapshot(user_id=1)

    assert snapshot.id is not None
    assert snapshot.snapshot_type == "weekly"
    assert snapshot.data is not None


@pytest.mark.asyncio
async def test_get_snapshots(db_session: AsyncSession):
    snapshot_service = SnapshotService(db_session)
    await snapshot_service.create_daily_snapshot(user_id=1)
    await snapshot_service.create_daily_snapshot(user_id=1)

    snapshots = await snapshot_service.get_snapshots(
        user_id=1, snapshot_type="daily"
    )

    assert len(snapshots) >= 1


@pytest.mark.asyncio
async def test_duplicate_snapshot_update(db_session: AsyncSession):
    snapshot_service = SnapshotService(db_session)
    snapshot1 = await snapshot_service.create_daily_snapshot(user_id=1)
    snapshot2 = await snapshot_service.create_daily_snapshot(user_id=1)

    assert snapshot1.id == snapshot2.id
