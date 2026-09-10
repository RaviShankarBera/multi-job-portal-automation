import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard_summary(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "jobs_found_total" in data
    assert "applications_total" in data
    assert "interviews_count" in data
    assert "offers_count" in data
    assert "match_rate" in data
    assert "conversion_rates" in data
    assert "top_skills_demand" in data
    assert "recent_activity" in data
    assert "recommended_jobs" in data
    assert "application_pipeline" in data


@pytest.mark.asyncio
async def test_get_weekly_performance(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/weekly")
    assert response.status_code == 200
    data = response.json()
    assert "period_start" in data
    assert "period_end" in data
    assert "daily_data" in data
    assert len(data["daily_data"]) == 7
    assert "total_applications" in data
    assert "total_responses" in data
    assert "total_interviews" in data


@pytest.mark.asyncio
async def test_get_application_funnel(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/funnel")
    assert response.status_code == 200
    data = response.json()
    assert "stages" in data
    assert "total" in data
    assert "conversion_rates" in data
    assert len(data["stages"]) > 0


@pytest.mark.asyncio
async def test_get_skills_demand(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/skills-demand")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_skills_demand_with_limit(authenticated_client: AsyncClient):
    response = await authenticated_client.get(
        "/api/v1/analytics/skills-demand?limit=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_get_job_market(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/job-market")
    assert response.status_code == 200
    data = response.json()
    assert "skills_demand" in data
    assert "top_job_titles" in data
    assert "salary_ranges" in data
    assert "companies_hiring" in data
    assert "locations_demand" in data
    assert "remote_percentage" in data
    assert "technology_trends" in data
    assert "industry_distribution" in data


@pytest.mark.asyncio
async def test_get_job_market_with_filter(authenticated_client: AsyncClient):
    response = await authenticated_client.get(
        "/api/v1/analytics/job-market?job_title=Engineer"
    )
    assert response.status_code == 200
    data = response.json()
    assert "salary_ranges" in data


@pytest.mark.asyncio
async def test_get_skill_coverage(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/skill-coverage")
    assert response.status_code == 200
    data = response.json()
    assert "covered_skills" in data
    assert "missing_skills" in data
    assert "coverage_percentage" in data
    assert "total_market_skills" in data
    assert "user_skills_count" in data


@pytest.mark.asyncio
async def test_get_skill_trends(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/analytics/skill-trends")
    assert response.status_code == 200
    data = response.json()
    assert "trending_up" in data
    assert "trending_down" in data
    assert "stable" in data


@pytest.mark.asyncio
async def test_get_skill_recommendations(authenticated_client: AsyncClient):
    response = await authenticated_client.get(
        "/api/v1/analytics/skill-recommendations"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_resume_performance(authenticated_client: AsyncClient):
    response = await authenticated_client.get(
        "/api/v1/analytics/resume-performance"
    )
    assert response.status_code == 200
    data = response.json()
    assert "ats_scores" in data
    assert "resume_performance" in data
    assert "correlation_insight" in data


@pytest.mark.asyncio
async def test_create_snapshot(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "daily"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snapshot_type"] == "daily"
    assert "snapshot_date" in data
    assert "data" in data


@pytest.mark.asyncio
async def test_create_weekly_snapshot(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "weekly"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["snapshot_type"] == "weekly"


@pytest.mark.asyncio
async def test_get_snapshots(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "daily"},
    )

    response = await authenticated_client.get("/api/v1/analytics/snapshots")
    assert response.status_code == 200
    data = response.json()
    assert "snapshots" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_snapshots_with_type_filter(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "daily"},
    )
    await authenticated_client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "weekly"},
    )

    response = await authenticated_client.get(
        "/api/v1/analytics/snapshots?snapshot_type=daily"
    )
    assert response.status_code == 200
    data = response.json()
    for snapshot in data["snapshots"]:
        assert snapshot["snapshot_type"] == "daily"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 401

    response = await client.get("/api/v1/analytics/weekly")
    assert response.status_code == 401

    response = await client.get("/api/v1/analytics/funnel")
    assert response.status_code == 401

    response = await client.get("/api/v1/analytics/job-market")
    assert response.status_code == 401

    response = await client.get("/api/v1/analytics/skill-coverage")
    assert response.status_code == 401

    response = await client.get("/api/v1/analytics/resume-performance")
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/analytics/snapshot",
        json={"snapshot_type": "daily"},
    )
    assert response.status_code == 401
