import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_profile_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/profile/")
    assert response.status_code == 404
    assert "Profile not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_profile(authenticated_client: AsyncClient):
    response = await authenticated_client.put(
        "/api/v1/profile/",
        json={
            "name": "Test Profile",
            "email": "test@example.com",
            "phone": "+1234567890",
            "location": "New York",
            "current_title": "Software Engineer",
            "target_title": "Senior Software Engineer",
            "years_of_experience": 5,
            "skills": ["Python", "FastAPI", "SQLAlchemy"],
            "technical_skills": ["Python", "JavaScript", "SQL"],
            "soft_skills": ["Communication", "Leadership"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Profile"
    assert data["current_title"] == "Software Engineer"
    assert "Python" in data["skills"]


@pytest.mark.asyncio
async def test_update_profile(authenticated_client: AsyncClient):
    # Create profile first
    await authenticated_client.put(
        "/api/v1/profile/",
        json={
            "name": "Original Name",
            "current_title": "Developer",
        },
    )

    # Update profile
    response = await authenticated_client.put(
        "/api/v1/profile/",
        json={
            "name": "Updated Name",
            "current_title": "Senior Developer",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["current_title"] == "Senior Developer"


@pytest.mark.asyncio
async def test_update_skills(authenticated_client: AsyncClient):
    # Create profile first
    await authenticated_client.put(
        "/api/v1/profile/",
        json={
            "name": "Skills Test",
        },
    )

    # Update skills
    response = await authenticated_client.post(
        "/api/v1/profile/skills",
        json={
            "skills": ["Python", "FastAPI", "React"],
            "technical_skills": ["Python", "JavaScript", "TypeScript"],
            "soft_skills": ["Problem Solving", "Team Work"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["skills"]
    assert "React" in data["skills"]
    assert "TypeScript" in data["technical_skills"]


@pytest.mark.asyncio
async def test_profile_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/profile/")
    assert response.status_code == 401