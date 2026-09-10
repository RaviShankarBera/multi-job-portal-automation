import pytest

from app.services.matching import JobMatchingService


@pytest.fixture
def matching_service():
    return JobMatchingService()


def test_calculate_skills_score_perfect_match(matching_service):
    user_skills = ["Python", "FastAPI", "SQL", "Docker"]
    job_required = ["Python", "FastAPI", "SQL"]
    job_preferred = ["Docker", "Kubernetes"]

    score = matching_service.calculate_skills_score(
        user_skills, job_required, job_preferred
    )
    assert score == 100.0


def test_calculate_skills_score_partial_match(matching_service):
    user_skills = ["Python", "JavaScript"]
    job_required = ["Python", "FastAPI", "SQL"]
    job_preferred = []

    score = matching_service.calculate_skills_score(
        user_skills, job_required, job_preferred
    )
    assert 30 <= score <= 70


def test_calculate_skills_score_no_match(matching_service):
    user_skills = ["Java", "Spring"]
    job_required = ["Python", "FastAPI"]
    job_preferred = []

    score = matching_service.calculate_skills_score(
        user_skills, job_required, job_preferred
    )
    assert score <= 50


def test_calculate_skills_score_no_requirements(matching_service):
    user_skills = ["Python"]
    job_required = []
    job_preferred = []

    score = matching_service.calculate_skills_score(
        user_skills, job_required, job_preferred
    )
    assert score == 70.0


def test_calculate_experience_score_meets_requirement(matching_service):
    score = matching_service.calculate_experience_score(5, 5)
    assert score == 100.0


def test_calculate_experience_score_exceeds_by_1(matching_service):
    score = matching_service.calculate_experience_score(6, 5)
    assert score == 100.0


def test_calculate_experience_score_exceeds_by_3(matching_service):
    score = matching_service.calculate_experience_score(8, 5)
    assert 70 <= score <= 90


def test_calculate_experience_score_exceeds_by_6(matching_service):
    score = matching_service.calculate_experience_score(11, 5)
    assert 50 <= score <= 70


def test_calculate_experience_score_short_by_1(matching_service):
    score = matching_service.calculate_experience_score(4, 5)
    assert score == 80.0


def test_calculate_experience_score_short_by_2(matching_service):
    score = matching_service.calculate_experience_score(3, 5)
    assert score == 60.0


def test_calculate_experience_score_no_requirement(matching_service):
    score = matching_service.calculate_experience_score(5, None)
    assert score == 70.0


def test_calculate_title_score_exact_match(matching_service):
    score = matching_service.calculate_title_score(
        "Software Engineer", "Software Engineer"
    )
    assert score >= 90


def test_calculate_title_score_senior_match(matching_service):
    score = matching_service.calculate_title_score(
        "Senior Software Engineer", "Software Engineer"
    )
    assert score >= 50


def test_calculate_title_score_no_match(matching_service):
    score = matching_service.calculate_title_score(
        "Marketing Manager", "Software Engineer"
    )
    assert score <= 50


def test_calculate_title_score_empty(matching_service):
    score = matching_service.calculate_title_score("", "Software Engineer")
    assert score == 50.0


def test_calculate_location_score_same_city(matching_service):
    score = matching_service.calculate_location_score(
        "San Francisco, CA", "San Francisco, CA", "onsite"
    )
    assert score == 100.0


def test_calculate_location_score_remote_match(matching_service):
    score = matching_service.calculate_location_score(
        "New York, NY", "Anywhere", "remote", "remote"
    )
    assert score >= 80


def test_calculate_location_score_different_city(matching_service):
    score = matching_service.calculate_location_score(
        "New York, NY", "Los Angeles, CA", "onsite"
    )
    assert score <= 60


def test_calculate_location_score_no_user_location(matching_service):
    score = matching_service.calculate_location_score(
        "", "San Francisco, CA", "onsite"
    )
    assert score == 60.0


def test_calculate_salary_score_within_range(matching_service):
    score = matching_service.calculate_salary_score(100000, 90000, 120000)
    assert score == 100.0


def test_calculate_salary_score_below_range(matching_service):
    score = matching_service.calculate_salary_score(80000, 90000, 120000)
    assert 50 <= score <= 90


def test_calculate_salary_score_above_range(matching_service):
    score = matching_service.calculate_salary_score(130000, 90000, 120000)
    assert 30 <= score <= 80


def test_calculate_salary_score_no_user_expectation(matching_service):
    score = matching_service.calculate_salary_score(None, 90000, 120000)
    assert score == 70.0


def test_calculate_salary_score_no_job_salary(matching_service):
    score = matching_service.calculate_salary_score(100000, None, None)
    assert score == 60.0


def test_calculate_certification_score_match(matching_service):
    score = matching_service.calculate_certification_score(
        ["AWS Certified", "PMP"],
        ["AWS Certified required", "PMP preferred"],
    )
    assert score >= 80


def test_calculate_certification_score_no_requirements(matching_service):
    score = matching_service.calculate_certification_score(
        ["AWS Certified"], []
    )
    assert score == 80.0


def test_calculate_overall_score(matching_service):
    scores = {
        "skills_score": 80.0,
        "experience_score": 90.0,
        "title_score": 70.0,
        "industry_score": 50.0,
        "location_score": 85.0,
        "salary_score": 75.0,
        "education_score": 60.0,
        "certification_score": 70.0,
    }

    overall = matching_service.calculate_overall_score(scores)
    assert 0 <= overall <= 100
    assert overall > 0


def test_calculate_overall_score_all_zero(matching_service):
    scores = {
        "skills_score": 0.0,
        "experience_score": 0.0,
        "title_score": 0.0,
        "industry_score": 0.0,
        "location_score": 0.0,
        "salary_score": 0.0,
        "education_score": 0.0,
        "certification_score": 0.0,
    }

    overall = matching_service.calculate_overall_score(scores)
    assert overall == 0.0


def test_generate_explanation_strong_match(matching_service):
    scores = {
        "skills_score": 90.0,
        "experience_score": 85.0,
        "title_score": 80.0,
        "location_score": 90.0,
        "salary_score": 85.0,
    }

    explanation = matching_service.generate_explanation(scores)
    assert len(explanation) > 0
    assert "Strong skills match" in explanation
    assert "well-suited" in explanation


def test_generate_explanation_weak_match(matching_service):
    scores = {
        "skills_score": 30.0,
        "experience_score": 20.0,
        "title_score": 40.0,
        "location_score": 30.0,
        "salary_score": 25.0,
    }

    explanation = matching_service.generate_explanation(scores)
    assert len(explanation) > 0
    assert "Limited skills match" in explanation


def test_weights_normalize(matching_service):
    custom_weights = {
        "skills": 2.0,
        "experience": 3.0,
    }
    service = JobMatchingService(weights=custom_weights)
    total = sum(service.weights.values())
    assert abs(total - 1.0) < 0.01
