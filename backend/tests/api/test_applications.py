import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Application Test Job",
            "company": "App Corp",
            "location": "App City",
        },
    )
    job_id = job_response.json()["id"]

    response = await authenticated_client.post(
        "/api/v1/applications/",
        json={
            "job_id": job_id,
            "notes": "Great opportunity",
            "source": "linkedin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "saved"
    assert data["source"] == "linkedin"
    assert data["notes"] == "Great opportunity"


@pytest.mark.asyncio
async def test_create_application_duplicate(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Dup App Test Job",
            "company": "Dup App Corp",
            "location": "Dup App City",
        },
    )
    job_id = job_response.json()["id"]

    await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )

    response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_applications(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "List App Test Job",
            "company": "List Corp",
            "location": "List City",
        },
    )
    job_id = job_response.json()["id"]

    await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )

    response = await authenticated_client.get("/api/v1/applications/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["applications"]) >= 1


@pytest.mark.asyncio
async def test_get_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Get App Test Job",
            "company": "Get Corp",
            "location": "Get City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/applications/{app_id}")
    assert response.status_code == 200
    assert response.json()["id"] == app_id
    assert response.json()["status"] == "saved"


@pytest.mark.asyncio
async def test_get_application_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/applications/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Update App Test Job",
            "company": "Update Corp",
            "location": "Update City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.put(
        f"/api/v1/applications/{app_id}",
        json={"notes": "Updated notes", "recruiter_name": "John Doe"},
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Updated notes"
    assert response.json()["recruiter_name"] == "John Doe"


@pytest.mark.asyncio
async def test_update_application_status(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Status Test Job",
            "company": "Status Corp",
            "location": "Status City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]
    assert create_response.json()["status"] == "saved"

    response = await authenticated_client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "interested"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "interested"


@pytest.mark.asyncio
async def test_update_application_status_invalid_transition(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Invalid Transition Job",
            "company": "Invalid Corp",
            "location": "Invalid City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "offer"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Submit Test Job",
            "company": "Submit Corp",
            "location": "Submit City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    await authenticated_client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "interested"},
    )
    await authenticated_client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "resume_tailored"},
    )
    await authenticated_client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "ready_to_apply"},
    )

    response = await authenticated_client.post(
        f"/api/v1/applications/{app_id}/submit",
        json={
            "submission_url": "https://example.com/apply/123",
            "notes": "Applied via portal",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "application_submitted"
    assert response.json()["submission_url"] == "https://example.com/apply/123"


@pytest.mark.asyncio
async def test_withdraw_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Withdraw Test Job",
            "company": "Withdraw Corp",
            "location": "Withdraw City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/applications/{app_id}")
    assert response.status_code == 204

    get_response = await authenticated_client.get(f"/api/v1/applications/{app_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "withdrawn"


@pytest.mark.asyncio
async def test_add_note(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Note Test Job",
            "company": "Note Corp",
            "location": "Note City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/applications/{app_id}/notes",
        json={"note": "Had a great phone screen today"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "note_added"
    assert data["description"] == "Had a great phone screen today"


@pytest.mark.asyncio
async def test_schedule_follow_up(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "FollowUp Test Job",
            "company": "FollowUp Corp",
            "location": "FollowUp City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.put(
        f"/api/v1/applications/{app_id}/follow-up",
        json={"follow_up_date": "2026-10-01T10:00:00Z"},
    )
    assert response.status_code == 200
    assert response.json()["next_follow_up"] is not None


@pytest.mark.asyncio
async def test_get_follow_ups(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "FollowUps List Job",
            "company": "FollowUps Corp",
            "location": "FollowUps City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    await authenticated_client.put(
        f"/api/v1/applications/{app_id}/follow-up",
        json={"follow_up_date": "2026-10-01T10:00:00Z"},
    )

    response = await authenticated_client.get("/api/v1/applications/follow-ups")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_application_stats(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Stats Test Job",
            "company": "Stats Corp",
            "location": "Stats City",
        },
    )
    job_id = job_response.json()["id"]

    await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )

    response = await authenticated_client.get("/api/v1/applications/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_applications" in data
    assert "by_status" in data
    assert "conversion_rates" in data
    assert "applications_this_week" in data
    assert "applications_this_month" in data
    assert data["total_applications"] >= 1


@pytest.mark.asyncio
async def test_get_pipeline(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Pipeline Test Job",
            "company": "Pipeline Corp",
            "location": "Pipeline City",
        },
    )
    job_id = job_response.json()["id"]

    await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )

    response = await authenticated_client.get("/api/v1/applications/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert "pipeline" in data
    assert "total" in data
    assert "saved" in data["pipeline"]


@pytest.mark.asyncio
async def test_get_application_events(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Events Test Job",
            "company": "Events Corp",
            "location": "Events City",
        },
    )
    job_id = job_response.json()["id"]

    create_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = create_response.json()["id"]

    response = await authenticated_client.get(
        f"/api/v1/applications/{app_id}/events"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["event_type"] == "created"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/applications/")
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/applications/",
        json={"job_id": 1},
    )
    assert response.status_code == 401
