import io
import os
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_resume_txt(authenticated_client: AsyncClient):
    file_content = b"""John Doe
john.doe@email.com | +1-555-0123 | linkedin.com/in/johndoe

Summary
Experienced software engineer with 5+ years of experience in Python and JavaScript.

Experience
Senior Developer at Tech Corp | Jan 2020 - Present
- Led development of microservices architecture
- Mentored junior developers

Education
Bachelor of Science in Computer Science | MIT | 2018

Skills
Python, JavaScript, React, Django, PostgreSQL, Docker, AWS

Certifications
AWS Certified Solutions Architect - Amazon Web Services | 2021
"""

    response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(file_content), "text/plain")},
        params={"title": "Test Resume"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Resume"
    assert data["original_filename"] == "resume.txt"
    assert data["file_type"] == "txt"
    assert data["is_primary"] is False


@pytest.mark.asyncio
async def test_upload_resume_with_tags(authenticated_client: AsyncClient):
    file_content = b"Simple resume content"
    response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(file_content), "text/plain")},
        params={"title": "Tagged Resume", "tags": "python,backend,senior"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == ["python", "backend", "senior"]


@pytest.mark.asyncio
async def test_upload_resume_invalid_extension(authenticated_client: AsyncClient):
    file_content = b"malicious content"
    response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.exe", io.BytesIO(file_content), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_resume_no_filename(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("", io.BytesIO(b"content"), "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_resumes_empty(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/resumes/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["resumes"] == []


@pytest.mark.asyncio
async def test_list_resumes_with_data(authenticated_client: AsyncClient):
    await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume1.txt", io.BytesIO(b"Resume 1"), "text/plain")},
    )
    await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume2.txt", io.BytesIO(b"Resume 2"), "text/plain")},
    )

    response = await authenticated_client.get("/api/v1/resumes/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["resumes"]) == 2


@pytest.mark.asyncio
async def test_get_resume(authenticated_client: AsyncClient):
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"Resume content"), "text/plain")},
        params={"title": "Get Test Resume"},
    )
    resume_id = upload_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/resumes/{resume_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == resume_id
    assert data["title"] == "Get Test Resume"


@pytest.mark.asyncio
async def test_get_resume_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/resumes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_resume(authenticated_client: AsyncClient):
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"Resume content"), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    response = await authenticated_client.delete(f"/api/v1/resumes/{resume_id}")
    assert response.status_code == 204

    get_response = await authenticated_client.get(f"/api/v1/resumes/{resume_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_resume_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.delete("/api/v1/resumes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_primary_resume(authenticated_client: AsyncClient):
    upload1 = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume1.txt", io.BytesIO(b"Resume 1"), "text/plain")},
    )
    upload2 = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume2.txt", io.BytesIO(b"Resume 2"), "text/plain")},
    )
    resume1_id = upload1.json()["id"]
    resume2_id = upload2.json()["id"]

    response = await authenticated_client.put(f"/api/v1/resumes/{resume1_id}/primary")
    assert response.status_code == 200
    assert response.json()["is_primary"] is True

    response = await authenticated_client.put(f"/api/v1/resumes/{resume2_id}/primary")
    assert response.status_code == 200
    assert response.json()["is_primary"] is True

    check1 = await authenticated_client.get(f"/api/v1/resumes/{resume1_id}")
    assert check1.json()["is_primary"] is False


@pytest.mark.asyncio
async def test_set_primary_resume_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.put("/api/v1/resumes/99999/primary")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_resume_version(authenticated_client: AsyncClient):
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"Resume content"), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    response = await authenticated_client.post(
        f"/api/v1/resumes/{resume_id}/versions",
        json={"job_id": None, "tailored_content": {"summary": "Tailored summary"}},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version_number"] == 1
    assert data["tailored_content"]["summary"] == "Tailored summary"


@pytest.mark.asyncio
async def test_get_resume_versions(authenticated_client: AsyncClient):
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"Resume content"), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    await authenticated_client.post(
        f"/api/v1/resumes/{resume_id}/versions",
        json={"tailored_content": {"version": 1}},
    )
    await authenticated_client.post(
        f"/api/v1/resumes/{resume_id}/versions",
        json={"tailored_content": {"version": 2}},
    )

    response = await authenticated_client.get(f"/api/v1/resumes/{resume_id}/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version_number"] == 2
    assert data[1]["version_number"] == 1


@pytest.mark.asyncio
async def test_get_ats_score(authenticated_client: AsyncClient):
    resume_content = b"""John Doe
john@email.com | 555-0123

Summary
Software engineer with Python and JavaScript experience.

Experience
Developer at Tech Corp | 2020 - Present
- Built REST APIs using Python and FastAPI
- Worked with PostgreSQL databases

Education
BS Computer Science | MIT | 2018

Skills
Python, JavaScript, React, FastAPI, PostgreSQL, Docker
"""
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(resume_content), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    job_description = "Looking for a Python developer with FastAPI and PostgreSQL experience."

    response = await authenticated_client.get(
        f"/api/v1/resumes/{resume_id}/ats-score",
        params={"job_description": job_description},
    )
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["ats_score"] <= 100
    assert 0 <= data["keyword_match"] <= 100
    assert isinstance(data["missing_keywords"], list)
    assert isinstance(data["suggestions"], list)
    assert isinstance(data["sections_present"], dict)


@pytest.mark.asyncio
async def test_get_ats_score_missing_description(authenticated_client: AsyncClient):
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"Resume"), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    response = await authenticated_client.get(f"/api/v1/resumes/{resume_id}/ats-score")
    assert response.status_code == 400
    assert "job_description" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reparse_resume(authenticated_client: AsyncClient):
    resume_content = b"""Jane Smith
jane@email.com | +1-555-0456

Summary
Data scientist specializing in machine learning.

Experience
ML Engineer at Data Inc | 2019 - Present

Skills
Python, TensorFlow, PyTorch, SQL
"""
    upload_response = await authenticated_client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(resume_content), "text/plain")},
    )
    resume_id = upload_response.json()["id"]

    response = await authenticated_client.post(f"/api/v1/resumes/{resume_id}/parse")
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_content"] is not None
    assert data["structured_data"] is not None


@pytest.mark.asyncio
async def test_resume_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/resumes/")
    assert response.status_code == 401
