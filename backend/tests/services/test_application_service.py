import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.user import User
from app.schemas.application import STATUS_PIPELINE, VALID_STATUSES
from app.services.application import ApplicationService


async def _create_test_user(db: AsyncSession) -> User:
    from passlib.hash import bcrypt

    user = User(
        email="test_service@example.com",
        hashed_password=bcrypt.hash("testpassword"),
        full_name="Test Service User",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _create_test_job(db: AsyncSession) -> Job:
    from app.services.job import JobService
    from app.schemas.job import JobCreate

    service = JobService(db)
    return await service.create_job(
        JobCreate(
            title="Service Test Job",
            company="Service Corp",
            location="Service City",
        )
    )


@pytest.mark.asyncio
async def test_create_application(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id,
        job_id=job.id,
        notes="Test application",
    )

    assert application.id is not None
    assert application.user_id == user.id
    assert application.job_id == job.id
    assert application.status == "saved"
    assert application.notes == "Test application"


@pytest.mark.asyncio
async def test_create_application_job_not_found(db_session: AsyncSession):
    user = await _create_test_user(db_session)

    service = ApplicationService(db_session)
    with pytest.raises(Exception):
        await service.create_application(user_id=user.id, job_id=99999)


@pytest.mark.asyncio
async def test_create_application_duplicate(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    await service.create_application(user_id=user.id, job_id=job.id)

    with pytest.raises(Exception):
        await service.create_application(user_id=user.id, job_id=job.id)


@pytest.mark.asyncio
async def test_get_application(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    fetched = await service.get_application(application.id, user.id)
    assert fetched.id == application.id
    assert fetched.status == "saved"


@pytest.mark.asyncio
async def test_get_application_not_found(db_session: AsyncSession):
    user = await _create_test_user(db_session)

    service = ApplicationService(db_session)
    with pytest.raises(Exception):
        await service.get_application(99999, user.id)


@pytest.mark.asyncio
async def test_get_user_applications(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    await service.create_application(user_id=user.id, job_id=job.id)

    applications, total = await service.get_user_applications(user.id)
    assert total >= 1
    assert len(applications) >= 1


@pytest.mark.asyncio
async def test_get_user_applications_with_status_filter(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    await service.create_application(user_id=user.id, job_id=job.id)

    applications, total = await service.get_user_applications(
        user.id, status_filter="saved"
    )
    assert total >= 1

    applications, total = await service.get_user_applications(
        user.id, status_filter="applied"
    )
    assert total == 0


@pytest.mark.asyncio
async def test_update_application_status(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    updated = await service.update_application_status(
        application.id, user.id, "interested"
    )
    assert updated.status == "interested"


@pytest.mark.asyncio
async def test_update_application_status_invalid_transition(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    with pytest.raises(Exception):
        await service.update_application_status(
            application.id, user.id, "offer"
        )


@pytest.mark.asyncio
async def test_update_application_status_creates_event(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    await service.update_application_status(
        application.id, user.id, "interested"
    )

    events = await service.get_application_events(application.id, user.id)
    status_events = [e for e in events if e.event_type == "status_change"]
    assert len(status_events) >= 1
    assert status_events[0].old_value == "saved"
    assert status_events[0].new_value == "interested"


@pytest.mark.asyncio
async def test_full_pipeline_flow(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    pipeline_steps = [
        "interested",
        "resume_tailored",
        "ready_to_apply",
        "application_submitted",
        "hr_viewed",
        "recruiter_contacted",
        "interview",
        "technical_round",
        "hr_round",
        "offer",
    ]

    for step in pipeline_steps:
        application = await service.update_application_status(
            application.id, user.id, step
        )
        assert application.status == step

    events = await service.get_application_events(application.id, user.id)
    assert len(events) >= len(pipeline_steps) + 1


@pytest.mark.asyncio
async def test_save_application(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.save_application(
        user_id=user.id, job_id=job.id, notes="Quick save"
    )

    assert application.status == "saved"
    assert application.notes == "Quick save"


@pytest.mark.asyncio
async def test_submit_application(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    await service.update_application_status(
        application.id, user.id, "interested"
    )
    await service.update_application_status(
        application.id, user.id, "resume_tailored"
    )
    await service.update_application_status(
        application.id, user.id, "ready_to_apply"
    )

    submitted = await service.submit_application(
        application.id,
        user.id,
        {"submission_url": "https://apply.example.com/123", "notes": "Applied"},
    )
    assert submitted.status == "application_submitted"
    assert submitted.submission_url == "https://apply.example.com/123"
    assert submitted.applied_date is not None


@pytest.mark.asyncio
async def test_withdraw_application(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    withdrawn = await service.withdraw_application(application.id, user.id)
    assert withdrawn.status == "withdrawn"


@pytest.mark.asyncio
async def test_add_note(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    event = await service.add_note(
        application.id, user.id, "Had a phone screen today"
    )
    assert event.event_type == "note_added"
    assert event.description == "Had a phone screen today"

    refreshed = await service.get_application(application.id, user.id)
    assert "Had a phone screen today" in refreshed.notes


@pytest.mark.asyncio
async def test_schedule_follow_up(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    follow_up_date = datetime.utcnow() + timedelta(days=7)
    updated = await service.schedule_follow_up(
        application.id, user.id, follow_up_date
    )
    assert updated.next_follow_up is not None


@pytest.mark.asyncio
async def test_get_upcoming_follow_ups(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    follow_up_date = datetime.utcnow() + timedelta(days=3)
    await service.schedule_follow_up(application.id, user.id, follow_up_date)

    follow_ups = await service.get_upcoming_follow_ups(user.id)
    assert len(follow_ups) >= 1
    assert any(f.id == application.id for f in follow_ups)


@pytest.mark.asyncio
async def test_get_application_stats(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    await service.create_application(user_id=user.id, job_id=job.id)

    stats = await service.get_application_stats(user.id)
    assert "total_applications" in stats
    assert "by_status" in stats
    assert "conversion_rates" in stats
    assert "applications_this_week" in stats
    assert "applications_this_month" in stats
    assert stats["total_applications"] >= 1
    assert "saved" in stats["by_status"]


@pytest.mark.asyncio
async def test_get_pipeline(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    await service.create_application(user_id=user.id, job_id=job.id)

    pipeline = await service.get_pipeline(user.id)
    assert "pipeline" in pipeline
    assert "total" in pipeline
    assert "saved" in pipeline["pipeline"]
    assert pipeline["total"] >= 1


@pytest.mark.asyncio
async def test_get_application_events(db_session: AsyncSession):
    user = await _create_test_user(db_session)
    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    application = await service.create_application(
        user_id=user.id, job_id=job.id
    )

    events = await service.get_application_events(application.id, user.id)
    assert len(events) >= 1
    assert events[0].event_type == "created"


@pytest.mark.asyncio
async def test_user_data_isolation(db_session: AsyncSession):
    user1 = User(
        email="user1_isolation@example.com",
        hashed_password="hashed",
        full_name="User 1",
    )
    user2 = User(
        email="user2_isolation@example.com",
        hashed_password="hashed",
        full_name="User 2",
    )
    db_session.add_all([user1, user2])
    await db_session.flush()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    job = await _create_test_job(db_session)

    service = ApplicationService(db_session)
    app1 = await service.create_application(user_id=user1.id, job_id=job.id)

    with pytest.raises(Exception):
        await service.get_application(app1.id, user2.id)

    applications, total = await service.get_user_applications(user2.id)
    assert total == 0
