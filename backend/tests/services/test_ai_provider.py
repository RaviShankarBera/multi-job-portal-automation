import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.factory import AIProviderFactory


@pytest.mark.asyncio
async def test_mock_provider_analyze_job_description():
    provider = MockAIProvider()
    result = await provider.analyze_job_description(
        "We are looking for a Python developer with 5 years of experience in Django and React."
    )

    assert isinstance(result, dict)
    assert "title" in result
    assert "required_skills" in result
    assert isinstance(result["required_skills"], list)
    assert len(result["required_skills"]) > 0


@pytest.mark.asyncio
async def test_mock_provider_match_resume_to_job():
    provider = MockAIProvider()
    resume_data = {
        "structured_data": {"skills": ["python", "django", "react", "sql"]}
    }
    job_data = {
        "required_skills": ["python", "django", "aws"]
    }

    result = await provider.match_resume_to_job(resume_data, job_data)

    assert isinstance(result, dict)
    assert "overall_score" in result
    assert "skills_score" in result
    assert "matching_skills" in result
    assert "missing_skills" in result
    assert isinstance(result["matching_skills"], list)
    assert isinstance(result["missing_skills"], list)


@pytest.mark.asyncio
async def test_mock_provider_tailor_resume():
    provider = MockAIProvider()
    resume_data = {"id": 1, "title": "Software Engineer"}
    job_data = {"id": 1, "title": "Senior Developer", "required_skills": ["python", "react"]}
    profile_data = {"current_title": "Developer", "years_of_experience": 5}

    result = await provider.tailor_resume(resume_data, job_data, profile_data)

    assert isinstance(result, dict)
    assert "tailored_summary" in result
    assert "tailored_skills" in result
    assert "changes_made" in result
    assert "ats_score" in result


@pytest.mark.asyncio
async def test_mock_provider_generate_cover_letter():
    provider = MockAIProvider()
    profile_data = {"name": "John Doe", "current_title": "Developer"}
    resume_data = {"structured_data": {"skills": ["python"]}}
    job_data = {"title": "Software Engineer", "company": "Tech Corp"}

    result = await provider.generate_cover_letter(profile_data, resume_data, job_data)

    assert isinstance(result, str)
    assert len(result) > 100
    assert "Tech Corp" in result


@pytest.mark.asyncio
async def test_mock_provider_generate_application_answers():
    provider = MockAIProvider()
    profile_data = {"current_title": "Developer"}
    job_data = {"title": "Engineer"}
    questions = ["Why are you interested?", "What are your strengths?"]

    result = await provider.generate_application_answers(profile_data, job_data, questions)

    assert isinstance(result, dict)
    assert "1" in result
    assert "2" in result


@pytest.mark.asyncio
async def test_mock_provider_analyze_skill_gap():
    provider = MockAIProvider()
    user_skills = ["python", "javascript", "react"]
    job_market_skills = ["python", "react", "aws", "docker", "kubernetes"]

    result = await provider.analyze_skill_gap(user_skills, job_market_skills)

    assert isinstance(result, dict)
    assert "strong_skills" in result
    assert "missing_skills" in result
    assert "overall_gap_score" in result
    assert "learning_recommendations" in result
    assert isinstance(result["missing_skills"], list)
    assert len(result["missing_skills"]) > 0


@pytest.mark.asyncio
async def test_mock_provider_generate_interview_questions():
    provider = MockAIProvider()
    job_data = {"title": "Developer", "required_skills": ["python"]}
    resume_data = {"structured_data": {"skills": ["python"]}}

    result = await provider.generate_interview_questions(job_data, resume_data)

    assert isinstance(result, list)
    assert len(result) > 0
    assert "question" in result[0]
    assert "category" in result[0]


@pytest.mark.asyncio
async def test_mock_provider_extract_job_keywords():
    provider = MockAIProvider()
    job_description = (
        "We need a Python developer with React experience. "
        "Must know SQL, AWS, Docker. Agile methodology experience preferred."
    )

    result = await provider.extract_job_keywords(job_description)

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(kw, str) for kw in result)


def test_factory_create_mock_provider():
    provider = AIProviderFactory.create("mock")
    assert isinstance(provider, MockAIProvider)


def test_factory_list_providers():
    providers = AIProviderFactory.list_providers()
    assert "mock" in providers
    assert "openai" in providers


def test_factory_unknown_provider():
    with pytest.raises(ValueError, match="Unknown AI provider"):
        AIProviderFactory.create("unknown_provider")


def test_factory_register_provider():
    AIProviderFactory.register_provider("custom", "app.services.ai.mock_provider.MockAIProvider")
    providers = AIProviderFactory.list_providers()
    assert "custom" in providers
    # Cleanup
    del AIProviderFactory._providers["custom"]
