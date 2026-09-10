import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_recruiter(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={
            "name": "Jane Smith",
            "company": "Tech Recruiting Inc",
            "email": "jane@techrecruiting.com",
            "phone": "+1-555-0123",
            "linkedin_url": "https://linkedin.com/in/janesmith",
            "role": "Senior Recruiter",
            "source": "linkedin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["company"] == "Tech Recruiting Inc"
    assert data["email"] == "jane@techrecruiting.com"
    assert data["role"] == "Senior Recruiter"


@pytest.mark.asyncio
async def test_list_recruiters(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Recruiter One", "company": "Company A"},
    )
    await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Recruiter Two", "company": "Company B"},
    )

    response = await authenticated_client.get("/api/v1/recruiters/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_recruiter(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Get Recruiter", "company": "Get Corp"},
    )
    recruiter_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/recruiters/{recruiter_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recruiter_id
    assert response.json()["name"] == "Get Recruiter"


@pytest.mark.asyncio
async def test_get_recruiter_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/recruiters/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_recruiter(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Update Recruiter", "company": "Old Corp"},
    )
    recruiter_id = create_response.json()["id"]

    response = await authenticated_client.put(
        f"/api/v1/recruiters/{recruiter_id}",
        json={"company": "New Corp", "email": "new@corp.com"},
    )
    assert response.status_code == 200
    assert response.json()["company"] == "New Corp"
    assert response.json()["email"] == "new@corp.com"
    assert response.json()["name"] == "Update Recruiter"


@pytest.mark.asyncio
async def test_delete_recruiter(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Delete Recruiter", "company": "Delete Corp"},
    )
    recruiter_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/recruiters/{recruiter_id}")
    assert response.status_code == 204

    get_response = await authenticated_client.get(f"/api/v1/recruiters/{recruiter_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_add_communication(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Comm Recruiter", "company": "Comm Corp"},
    )
    recruiter_id = create_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/recruiters/{recruiter_id}/communications",
        json={
            "type": "email",
            "direction": "outbound",
            "subject": "Following up on application",
            "content": "Hi, I wanted to follow up on my recent application.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "email"
    assert data["direction"] == "outbound"
    assert data["subject"] == "Following up on application"


@pytest.mark.asyncio
async def test_get_communications(authenticated_client: AsyncClient):
    create_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Get Comm Recruiter", "company": "Get Comm Corp"},
    )
    recruiter_id = create_response.json()["id"]

    await authenticated_client.post(
        f"/api/v1/recruiters/{recruiter_id}/communications",
        json={
            "type": "phone",
            "direction": "inbound",
            "content": "Received a call from the recruiter.",
        },
    )
    await authenticated_client.post(
        f"/api/v1/recruiters/{recruiter_id}/communications",
        json={
            "type": "linkedin",
            "direction": "outbound",
            "subject": "Connection request",
            "content": "Connected on LinkedIn.",
        },
    )

    response = await authenticated_client.get(
        f"/api/v1/recruiters/{recruiter_id}/communications"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_add_communication_with_application(authenticated_client: AsyncClient):
    job_response = await authenticated_client.post(
        "/api/v1/jobs/",
        json={
            "title": "Comm App Job",
            "company": "Comm App Corp",
            "location": "Comm App City",
        },
    )
    job_id = job_response.json()["id"]

    app_response = await authenticated_client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
    )
    app_id = app_response.json()["id"]

    recruiter_response = await authenticated_client.post(
        "/api/v1/recruiters/",
        json={"name": "Linked Recruiter", "company": "Linked Corp"},
    )
    recruiter_id = recruiter_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/recruiters/{recruiter_id}/communications",
        json={
            "application_id": app_id,
            "type": "email",
            "direction": "inbound",
            "subject": "Interview Scheduled",
            "content": "Your interview has been scheduled for next week.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["application_id"] == app_id


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/recruiters/")
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/recruiters/",
        json={"name": "Test"},
    )
    assert response.status_code == 401
