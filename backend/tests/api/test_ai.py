import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_job_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/analyze-job",
        json={"job_description": "We are looking for a Python developer with 5 years of experience."},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_job(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/analyze-job",
        json={
            "job_description": (
                "We are looking for a Senior Python Developer with 5+ years of experience. "
                "Required skills: Python, Django, PostgreSQL, AWS. "
                "Nice to have: Docker, Kubernetes, React. "
                "Remote position, full-time. Salary: $120,000 - $160,000."
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "required_skills" in data
    assert isinstance(data["required_skills"], list)


@pytest.mark.asyncio
async def test_tailor_resume_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/tailor-resume",
        json={"resume_id": 1, "job_id": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tailor_resume_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/tailor-resume",
        json={"resume_id": 999, "job_id": 999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cover_letter_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/cover-letter",
        json={"resume_id": 1, "job_id": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cover_letter_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/cover-letter",
        json={"resume_id": 999, "job_id": 999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_skill_gap_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/skill-gap",
        json={"target_role": "Software Engineer"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_skill_gap_no_profile(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/skill-gap",
        json={"target_role": "Software Engineer"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_interview_questions_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/interview-questions",
        json={"job_id": 1, "resume_id": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_interview_questions_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/interview-questions",
        json={"job_id": 999, "resume_id": 999},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_extract_keywords_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/extract-keywords",
        json={"job_description": "Python developer needed with React experience."},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_extract_keywords(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/extract-keywords",
        json={
            "job_description": (
                "We need a Python developer with React experience. "
                "Must know SQL, AWS, Docker. Agile methodology preferred."
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "keywords" in data
    assert "count" in data
    assert isinstance(data["keywords"], list)
    assert data["count"] > 0


@pytest.mark.asyncio
async def test_company_analysis_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/ai/company-analysis",
        json={"company_name": "Google"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_company_analysis(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/ai/company-analysis",
        json={"company_name": "Google"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "overview" in data
    assert "industry" in data
