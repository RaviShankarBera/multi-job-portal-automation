import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.resume_tailoring import ResumeTailoringService
from app.services.ai.mock_provider import MockAIProvider


@pytest.mark.asyncio
async def test_optimize_skills_section():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.ai_provider = provider

    skills = ["java", "python", "react", "sql", "docker"]
    job_keywords = ["python", "react", "aws", "docker"]

    result = await service.optimize_skills_section(skills, job_keywords)

    assert isinstance(result, list)
    assert len(result) == len(skills)
    # Job-matching skills should be first
    python_idx = result.index("python")
    react_idx = result.index("react")
    docker_idx = result.index("docker")
    java_idx = result.index("java")
    assert python_idx < java_idx
    assert react_idx < java_idx
    assert docker_idx < java_idx


@pytest.mark.asyncio
async def test_tailor_resume_for_job_missing_user():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.db = MagicMock()
    service.ai_provider = provider

    # Mock db.execute to return None for user query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    service.db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="User .* not found"):
        await service.tailor_resume_for_job(user_id=999, resume_id=1, job_id=1)


@pytest.mark.asyncio
async def test_tailor_resume_for_job_missing_resume():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.db = MagicMock()
    service.ai_provider = provider

    # Create mock objects
    mock_user = MagicMock()
    mock_user.id = 1
    mock_profile = MagicMock()
    mock_profile.user_id = 1

    call_count = [0]

    async def mock_execute(query):
        call_count[0] += 1
        mock_result = MagicMock()
        if call_count[0] == 1:  # User query
            mock_result.scalar_one_or_none.return_value = mock_user
        elif call_count[0] == 2:  # Profile query
            mock_result.scalar_one_or_none.return_value = mock_profile
        else:  # Resume query
            mock_result.scalar_one_or_none.return_value = None
        return mock_result

    service.db.execute = mock_execute

    with pytest.raises(ValueError, match="Resume .* not found"):
        await service.tailor_resume_for_job(user_id=1, resume_id=999, job_id=1)


def test_serialize_resume():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.ai_provider = provider

    mock_resume = MagicMock()
    mock_resume.id = 1
    mock_resume.title = "Software Engineer"
    mock_resume.parsed_content = "Content here"
    mock_resume.structured_data = {"skills": ["python"]}
    mock_resume.tags = ["tech"]

    result = service._serialize_resume(mock_resume)

    assert result["id"] == 1
    assert result["title"] == "Software Engineer"
    assert result["parsed_content"] == "Content here"
    assert result["structured_data"] == {"skills": ["python"]}
    assert result["tags"] == ["tech"]


def test_serialize_job():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.ai_provider = provider

    mock_job = MagicMock()
    mock_job.id = 1
    mock_job.title = "Senior Developer"
    mock_job.company = "Tech Corp"
    mock_job.location = "Remote"
    mock_job.remote_status = "remote"
    mock_job.description = "Job description"
    mock_job.required_skills = ["python", "react"]
    mock_job.preferred_skills = ["aws"]
    mock_job.responsibilities = ["Build things"]
    mock_job.qualifications = ["BS in CS"]
    mock_job.experience_years = 5
    mock_job.salary_min = 100000
    mock_job.salary_max = 150000
    mock_job.employment_type = "full-time"

    result = service._serialize_job(mock_job)

    assert result["id"] == 1
    assert result["title"] == "Senior Developer"
    assert result["company"] == "Tech Corp"
    assert result["required_skills"] == ["python", "react"]


def test_serialize_profile():
    provider = MockAIProvider()
    service = ResumeTailoringService.__new__(ResumeTailoringService)
    service.ai_provider = provider

    mock_profile = MagicMock()
    mock_profile.name = "John Doe"
    mock_profile.email = "john@example.com"
    mock_profile.phone = "555-0123"
    mock_profile.location = "New York"
    mock_profile.current_title = "Developer"
    mock_profile.target_title = "Senior Developer"
    mock_profile.years_of_experience = 5
    mock_profile.skills = ["python", "react"]
    mock_profile.technical_skills = ["sql", "aws"]
    mock_profile.soft_skills = ["leadership"]
    mock_profile.certifications = []
    mock_profile.education = [{"degree": "BS CS"}]
    mock_profile.companies_worked = ["Company A"]
    mock_profile.job_history = []

    result = service._serialize_profile(mock_profile)

    assert result["name"] == "John Doe"
    assert result["current_title"] == "Developer"
    assert result["skills"] == ["python", "react"]
    assert result["technical_skills"] == ["sql", "aws"]
    assert result["education"] == [{"degree": "BS CS"}]
