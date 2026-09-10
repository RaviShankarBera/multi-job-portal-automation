import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, SavedJob, JobMatch
from app.schemas.job import JobCreate, JobSearchParams, SavedJobCreate
from app.services.job import JobService


@pytest.mark.asyncio
async def test_generate_duplicate_hash(db_session: AsyncSession):
    service = JobService(db_session)
    hash1 = service.generate_duplicate_hash("Software Engineer", "Tech Corp", "San Francisco")
    hash2 = service.generate_duplicate_hash("software engineer", "tech corp", "san francisco")
    hash3 = service.generate_duplicate_hash("Different Title", "Tech Corp", "San Francisco")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


@pytest.mark.asyncio
async def test_create_job(db_session: AsyncSession):
    service = JobService(db_session)
    data = JobCreate(
        title="Test Engineer",
        company="Test Corp",
        location="Test City",
        description="Test description",
        employment_type="full-time",
        remote_status="remote",
        required_skills=["Python", "FastAPI"],
    )

    job = await service.create_job(data)
    assert job.id is not None
    assert job.title == "Test Engineer"
    assert job.company == "Test Corp"
    assert job.source == "manual"
    assert job.duplicate_hash is not None


@pytest.mark.asyncio
async def test_create_job_duplicate(db_session: AsyncSession):
    service = JobService(db_session)
    data = JobCreate(
        title="Dup Engineer",
        company="Dup Corp",
        location="Dup City",
    )

    job1 = await service.create_job(data)
    assert job1.id is not None

    with pytest.raises(Exception):
        await service.create_job(data)


@pytest.mark.asyncio
async def test_get_job(db_session: AsyncSession):
    service = JobService(db_session)
    data = JobCreate(
        title="Get Test Job",
        company="Get Corp",
        location="Get City",
    )

    job = await service.create_job(data)
    fetched = await service.get_job(job.id)
    assert fetched.id == job.id
    assert fetched.title == "Get Test Job"


@pytest.mark.asyncio
async def test_get_job_not_found(db_session: AsyncSession):
    service = JobService(db_session)
    with pytest.raises(Exception):
        await service.get_job(99999)


@pytest.mark.asyncio
async def test_search_jobs(db_session: AsyncSession):
    service = JobService(db_session)

    await service.create_job(
        JobCreate(
            title="Python Developer",
            company="Python Corp",
            location="Python City",
            required_skills=["Python"],
        )
    )
    await service.create_job(
        JobCreate(
            title="Java Developer",
            company="Java Corp",
            location="Java City",
            required_skills=["Java"],
        )
    )

    params = JobSearchParams(keywords="Python")
    jobs, total = await service.search_jobs(user_id=1, params=params)
    assert total >= 1
    assert any("Python" in job.title for job in jobs)


@pytest.mark.asyncio
async def test_search_jobs_by_location(db_session: AsyncSession):
    service = JobService(db_session)

    await service.create_job(
        JobCreate(
            title="SF Job",
            company="SF Corp",
            location="San Francisco, CA",
        )
    )
    await service.create_job(
        JobCreate(
            title="NYC Job",
            company="NYC Corp",
            location="New York, NY",
        )
    )

    params = JobSearchParams(location="San Francisco")
    jobs, total = await service.search_jobs(user_id=1, params=params)
    assert total >= 1
    assert all("San Francisco" in job.location for job in jobs)


@pytest.mark.asyncio
async def test_save_job(db_session: AsyncSession):
    service = JobService(db_session)
    job = await service.create_job(
        JobCreate(
            title="Save Test",
            company="Save Corp",
            location="Save City",
        )
    )

    saved = await service.save_job(user_id=1, job_id=job.id, notes="Great job!")
    assert saved.id is not None
    assert saved.user_id == 1
    assert saved.job_id == job.id
    assert saved.notes == "Great job!"


@pytest.mark.asyncio
async def test_unsave_job(db_session: AsyncSession):
    service = JobService(db_session)
    job = await service.create_job(
        JobCreate(
            title="Unsave Test",
            company="Unsave Corp",
            location="Unsave City",
        )
    )

    await service.save_job(user_id=1, job_id=job.id)
    result = await service.unsave_job(user_id=1, job_id=job.id)
    assert result is True

    result = await service.unsave_job(user_id=1, job_id=job.id)
    assert result is False


@pytest.mark.asyncio
async def test_get_saved_jobs(db_session: AsyncSession):
    service = JobService(db_session)
    job1 = await service.create_job(
        JobCreate(title="Saved 1", company="C1", location="L1")
    )
    job2 = await service.create_job(
        JobCreate(title="Saved 2", company="C2", location="L2")
    )

    await service.save_job(user_id=1, job_id=job1.id)
    await service.save_job(user_id=1, job_id=job2.id)

    saved = await service.get_saved_jobs(user_id=1)
    assert len(saved) == 2


@pytest.mark.asyncio
async def test_deduplicate_jobs(db_session: AsyncSession):
    service = JobService(db_session)

    job1 = await service.create_job(
        JobCreate(title="Dedup 1", company="Dedup Corp", location="Dedup City")
    )

    jobs = [job1, job1]
    unique = await service.deduplicate_jobs(jobs)
    assert len(unique) == 1


@pytest.mark.asyncio
async def test_get_job_stats(db_session: AsyncSession):
    service = JobService(db_session)

    await service.create_job(
        JobCreate(title="Stats 1", company="S1", location="L1")
    )
    await service.create_job(
        JobCreate(title="Stats 2", company="S2", location="L2")
    )

    job = await service.create_job(
        JobCreate(title="Stats 3", company="S3", location="L3")
    )
    await service.save_job(user_id=1, job_id=job.id)

    stats = await service.get_job_stats(user_id=1)
    assert stats["total_jobs"] >= 3
    assert stats["saved_jobs_count"] >= 1
    assert "jobs_by_source" in stats
    assert "jobs_by_status" in stats
