import io
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.services.resume import ResumeService


class MockUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self.size = len(content)

    async def read(self) -> bytes:
        return self._content

    async def seek(self, offset: int):
        pass


@pytest.mark.asyncio
async def test_upload_resume_txt(db_session: AsyncSession):
    service = ResumeService(db_session)
    file = MockUploadFile("test_resume.txt", b"Hello World Resume Content")

    resume = await service.upload_resume(user_id=1, file=file, title="Test Resume")
    assert resume.id is not None
    assert resume.title == "Test Resume"
    assert resume.original_filename == "test_resume.txt"
    assert resume.file_type == "txt"
    assert resume.user_id == 1


@pytest.mark.asyncio
async def test_upload_resume_default_title(db_session: AsyncSession):
    service = ResumeService(db_session)
    file = MockUploadFile("my_resume.txt", b"Resume content")

    resume = await service.upload_resume(user_id=1, file=file)
    assert resume.title == "my_resume"


@pytest.mark.asyncio
async def test_upload_resume_invalid_extension(db_session: AsyncSession):
    service = ResumeService(db_session)
    file = MockUploadFile("resume.exe", b"Malicious content")

    with pytest.raises(Exception) as exc_info:
        await service.upload_resume(user_id=1, file=file)
    assert "not allowed" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_resume_no_filename(db_session: AsyncSession):
    service = ResumeService(db_session)
    file = MockUploadFile("", b"content")

    with pytest.raises(Exception) as exc_info:
        await service.upload_resume(user_id=1, file=file)
    assert "No filename" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_resumes_empty(db_session: AsyncSession):
    service = ResumeService(db_session)
    resumes = await service.get_resumes(user_id=1)
    assert resumes == []


@pytest.mark.asyncio
async def test_get_resumes(db_session: AsyncSession):
    service = ResumeService(db_session)

    await service.upload_resume(user_id=1, file=MockUploadFile("r1.txt", b"Content 1"), title="Resume 1")
    await service.upload_resume(user_id=1, file=MockUploadFile("r2.txt", b"Content 2"), title="Resume 2")

    resumes = await service.get_resumes(user_id=1)
    assert len(resumes) == 2


@pytest.mark.asyncio
async def test_get_resumes_by_user(db_session: AsyncSession):
    service = ResumeService(db_session)

    await service.upload_resume(user_id=1, file=MockUploadFile("r1.txt", b"User 1"), title="U1")
    await service.upload_resume(user_id=2, file=MockUploadFile("r2.txt", b"User 2"), title="U2")

    resumes_user1 = await service.get_resumes(user_id=1)
    resumes_user2 = await service.get_resumes(user_id=2)
    assert len(resumes_user1) == 1
    assert len(resumes_user2) == 1
    assert resumes_user1[0].user_id == 1
    assert resumes_user2[0].user_id == 2


@pytest.mark.asyncio
async def test_get_resume(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="My Resume")

    found = await service.get_resume(resume.id, user_id=1)
    assert found.id == resume.id
    assert found.title == "My Resume"


@pytest.mark.asyncio
async def test_get_resume_not_found(db_session: AsyncSession):
    service = ResumeService(db_session)
    with pytest.raises(Exception) as exc_info:
        await service.get_resume(99999, user_id=1)
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_resume_wrong_user(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="User 1 Resume")

    with pytest.raises(Exception) as exc_info:
        await service.get_resume(resume.id, user_id=2)
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_delete_resume(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="To Delete")

    result = await service.delete_resume(resume.id, user_id=1)
    assert result is True

    with pytest.raises(Exception):
        await service.get_resume(resume.id, user_id=1)


@pytest.mark.asyncio
async def test_delete_resume_not_found(db_session: AsyncSession):
    service = ResumeService(db_session)
    with pytest.raises(Exception):
        await service.delete_resume(99999, user_id=1)


@pytest.mark.asyncio
async def test_set_primary_resume(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume1 = await service.upload_resume(user_id=1, file=MockUploadFile("r1.txt", b"Content 1"), title="Resume 1")
    resume2 = await service.upload_resume(user_id=1, file=MockUploadFile("r2.txt", b"Content 2"), title="Resume 2")

    result = await service.set_primary_resume(resume1.id, user_id=1)
    assert result.is_primary is True

    await service.set_primary_resume(resume2.id, user_id=1)

    refreshed1 = await service.get_resume(resume1.id, user_id=1)
    refreshed2 = await service.get_resume(resume2.id, user_id=1)
    assert refreshed1.is_primary is False
    assert refreshed2.is_primary is True


@pytest.mark.asyncio
async def test_create_version(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="Versioned")

    version = await service.create_version(
        resume_id=resume.id, user_id=1, job_id=None, tailored_content={"summary": "Tailored"}
    )
    assert version.version_number == 1
    assert version.tailored_content["summary"] == "Tailored"
    assert version.resume_id == resume.id


@pytest.mark.asyncio
async def test_create_multiple_versions(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="Multi")

    v1 = await service.create_version(resume_id=resume.id, user_id=1, tailored_content={"v": 1})
    v2 = await service.create_version(resume_id=resume.id, user_id=1, tailored_content={"v": 2})
    v3 = await service.create_version(resume_id=resume.id, user_id=1, tailored_content={"v": 3})

    assert v1.version_number == 1
    assert v2.version_number == 2
    assert v3.version_number == 3


@pytest.mark.asyncio
async def test_get_versions(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="Versioned")

    await service.create_version(resume_id=resume.id, user_id=1)
    await service.create_version(resume_id=resume.id, user_id=1)

    versions = await service.get_versions(resume.id, user_id=1)
    assert len(versions) == 2
    assert versions[0].version_number == 2
    assert versions[1].version_number == 1


@pytest.mark.asyncio
async def test_get_versions_empty(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(user_id=1, file=MockUploadFile("r.txt", b"Content"), title="Empty")

    versions = await service.get_versions(resume.id, user_id=1)
    assert versions == []


@pytest.mark.asyncio
async def test_reparse_resume(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(
        user_id=1,
        file=MockUploadFile("r.txt", b"John Doe\njohn@email.com\nPython developer"),
        title="Reparsed",
    )

    result = await service.reparse_resume(resume.id, user_id=1)
    assert result.parsed_content is not None
    assert result.structured_data is not None


@pytest.mark.asyncio
async def test_calculate_ats_score(db_session: AsyncSession):
    service = ResumeService(db_session)
    resume = await service.upload_resume(
        user_id=1,
        file=MockUploadFile("r.txt", b"Python developer with Django experience"),
        title="ATS Test",
    )

    result = await service.calculate_ats_score(
        resume.id, user_id=1, job_description="Python Django developer needed"
    )
    assert 0 <= result.ats_score <= 100
    assert 0 <= result.keyword_match <= 100
    assert isinstance(result.missing_keywords, list)
    assert isinstance(result.suggestions, list)
    assert isinstance(result.sections_present, dict)


@pytest.mark.asyncio
async def test_parse_resume_content_txt():
    service = ResumeService.__new__(ResumeService)

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("John Doe\njohn@email.com\n555-0123\nPython\nReact")
        tmp_path = f.name

    try:
        result = await service.parse_resume_content(tmp_path, "txt")
        assert "raw_text" in result
        assert "contact_info" in result
        assert result["contact_info"]["email"] == "john@email.com"
        assert result["contact_info"]["phone"] == "555-0123"
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_extract_contact_info():
    service = ResumeService.__new__(ResumeService)

    text = "Contact: john.doe@email.com, +1-555-1234, linkedin.com/in/johndoe, github.com/johndoe"
    contact = service._extract_contact_info(text)

    assert contact["email"] == "john.doe@email.com"
    assert contact["phone"] == "+1-555-1234"
    assert "linkedin.com/in/johndoe" in contact["linkedin"]
    assert "github.com/johndoe" in contact["github"]


@pytest.mark.asyncio
async def test_extract_skills():
    service = ResumeService.__new__(ResumeService)

    text = "Skills: Python, JavaScript, React, Django, PostgreSQL, Docker, AWS"
    skills = service._extract_skills(text)

    assert "python" in [s.lower() for s in skills]
    assert "javascript" in [s.lower() for s in skills]
    assert "react" in [s.lower() for s in skills]
    assert "docker" in [s.lower() for s in skills]


@pytest.mark.asyncio
async def test_extract_keywords():
    service = ResumeService.__new__(ResumeService)

    keywords = service._extract_keywords("Python developer with experience in Django and REST APIs")
    assert "python" in keywords
    assert "developer" in keywords
    assert "django" in keywords
    assert "experience" in keywords
    assert "python" in keywords
