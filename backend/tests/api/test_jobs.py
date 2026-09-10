import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_job(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "description": "A great software engineering position",
            "employment_type": "full-time",
            "remote_status": "hybrid",
            "required_skills": ["Python", "FastAPI", "SQL"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Software Engineer"
    assert data["company"] == "Tech Corp"
    assert data["location"] == "San Francisco, CA"
    assert data["source"] == "manual"
    assert data["duplicate_hash"] is not None


@pytest.mark.asyncio
async def test_create_job_duplicate(authenticated_client: AsyncClient):
    job_data = {
        "title": "Duplicate Test Job",
        "company": "Test Corp",
        "location": "New York, NY",
    }

    response1 = await authenticated_client.post("/api/v1/jobs/", json=job_data)
    assert response1.status_code == 201

    response2 = await authenticated_client.post("/api/v1/jobs/", json=job_data)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_list_jobs(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "List Test Job 1",
            "company": "Company A",
            "location": "City A",
        },
    )
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "List Test Job 2",
            "company": "Company B",
            "location": "City B",
        },
    )

    response = await authenticated_client.get("/api/v1/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["jobs"]) >= 2
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_get_job(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Get Test Job",
            "company": "Get Corp",
            "location": "Get City",
        },
    )
    job_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["title"] == "Get Test Job"


@pytest.mark.asyncio
async def test_get_job_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/jobs/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_job(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Update Test Job",
            "company": "Update Corp",
            "location": "Update City",
        },
    )
    job_id = create_response.json()["id"]

    response = await authenticated_client.put(
        f"/api/v1/jobs/{job_id}",
        json={"title": "Updated Job Title"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Job Title"
    assert response.json()["company"] == "Update Corp"


@pytest.mark.asyncio
async def test_delete_job(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Delete Test Job",
            "company": "Delete Corp",
            "location": "Delete City",
        },
    )
    job_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204

    get_response = await authenticated_client.get(f"/api/v1/jobs/{job_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_search_jobs(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Python Developer",
            "company": "Python Corp",
            "location": "Python City",
            "required_skills": ["Python", "Django"],
        },
    )
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Java Developer",
            "company": "Java Corp",
            "location": "Java City",
            "required_skills": ["Java", "Spring"],
        },
    )

    response = await authenticated_client.post(
        "/api/v1/jobs/search",
        json={"keywords": "Python"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Python" in job["title"] for job in data["jobs"])


@pytest.mark.asyncio
async def test_search_jobs_filters(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Remote Engineer",
            "company": "Remote Corp",
            "location": "Anywhere",
            "remote_status": "remote",
            "salary_min": 100000,
            "salary_max": 150000,
        },
    )

    response = await authenticated_client.post(
        "/api/v1/jobs/search",
        json={"remote": "remote", "salary_min": 90000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_save_job(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Save Test Job",
            "company": "Save Corp",
            "location": "Save City",
        },
    )
    job_id = create_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/jobs/{job_id}/save",
        json={"notes": "Great opportunity!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == job_id
    assert data["notes"] == "Great opportunity!"


@pytest.mark.asyncio
async def test_save_job_duplicate(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Save Dup Job",
            "company": "Save Dup Corp",
            "location": "Save Dup City",
        },
    )
    job_id = create_response.json()["id"]

    await authenticated_client.post(f"/api/v1/jobs/{job_id}/save")
    response = await authenticated_client.post(f"/api/v1/jobs/{job_id}/save")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_unsave_job(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Unsave Test Job",
            "company": "Unsave Corp",
            "location": "Unsave City",
        },
    )
    job_id = create_response.json()["id"]

    await authenticated_client.post(f"/api/v1/jobs/{job_id}/save")

    response = await authenticated_client.delete(f"/api/v1/jobs/{job_id}/save")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_saved_jobs(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Saved Jobs Test",
            "company": "Saved Corp",
            "location": "Saved City",
        },
    )
    job_id = create_response.json()["id"]

    await authenticated_client.post(f"/api/v1/jobs/{job_id}/save")

    response = await authenticated_client.get("/api/v1/jobs/saved")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(sj["job_id"] == job_id for sj in data)


@pytest.mark.asyncio
async def test_calculate_match(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/profile/",
        json={
            "skills": ["Python", "FastAPI", "SQL"],
            "years_of_experience": 5,
            "target_title": "Senior Software Engineer",
            "expected_salary": 130000,
            "location": "San Francisco, CA",
            "remote_preference": "hybrid",
        },
    )

    create_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Senior Software Engineer",
            "company": "Match Corp",
            "location": "San Francisco, CA",
            "remote_status": "hybrid",
            "salary_min": 120000,
            "salary_max": 160000,
            "experience_years": 5,
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
            "preferred_skills": ["Docker", "Kubernetes"],
        },
    )
    job_id = create_response.json()["id"]

    response = await authenticated_client.post(f"/api/v1/jobs/{job_id}/match")
    assert response.status_code == 201
    data = response.json()
    assert 0 <= data["overall_score"] <= 100
    assert 0 <= data["skills_score"] <= 100
    assert data["explanation"] is not None


@pytest.mark.asyncio
async def test_job_stats(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Stats Job 1",
            "company": "Stats Corp 1",
            "location": "Stats City 1",
        },
    )

    response = await authenticated_client.get("/api/v1/jobs/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "saved_jobs_count" in data
    assert "matched_jobs_count" in data
    assert data["total_jobs"] >= 1


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/jobs/")
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/jobs/",
        json={"title": "Test", "company": "Test", "location": "Test"},
    )
    assert response.status_code == 401
