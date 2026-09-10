import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.automation.runner import AutomationRunner
from app.services.automation import AutomationMode, AutomationStatus


@pytest.fixture
def runner():
    return AutomationRunner()


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestAutomationRunner:
    @pytest.mark.asyncio
    async def test_run_search_creates_run(self, runner):
        """Test that run_search creates an AutomationRun"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.services.automation.runner.AdapterFactory"
            ) as mock_factory_cls:
                mock_adapter = AsyncMock()
                mock_adapter.search_jobs.return_value = [
                    {"title": "Test Job", "company": "Test Co", "location": "NYC"}
                ]
                mock_factory_cls.create.return_value = mock_adapter

                run = await runner.run_search(
                    user_id=1,
                    portal="linkedin",
                    params={"keywords": "python developer"},
                )

                assert run is not None
                assert run.portal == "linkedin"
                assert run.status == AutomationStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_run_search_handles_failure(self, runner):
        """Test that run_search handles failures properly"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.services.automation.runner.AdapterFactory"
            ) as mock_factory_cls:
                mock_adapter = AsyncMock()
                mock_adapter.search_jobs.side_effect = Exception("Search failed")
                mock_factory_cls.create.return_value = mock_adapter

                run = await runner.run_search(
                    user_id=1,
                    portal="linkedin",
                    params={"keywords": "python developer"},
                )

                assert run is not None
                assert run.status == AutomationStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_application_creates_run(self, runner):
        """Test that run_application creates an AutomationRun"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.services.automation.runner.AdapterFactory"
            ) as mock_factory_cls:
                mock_adapter = AsyncMock()
                mock_adapter.open_job.return_value = {"title": "Test Job"}
                mock_adapter.start_application.return_value = {"status": "started"}
                mock_adapter.fill_application.return_value = {"status": "filled"}
                mock_adapter.upload_resume.return_value = True
                mock_adapter.submit_application.return_value = {"status": "submitted"}
                mock_adapter.capture_confirmation.return_value = {
                    "status": "confirmed"
                }
                mock_factory_cls.create.return_value = mock_adapter

                # Mock the job query
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = MagicMock(
                    id=1, url="http://example.com/job"
                )
                mock_session.execute.return_value = mock_result

                run = await runner.run_application(
                    user_id=1,
                    job_id=1,
                    portal="linkedin",
                    mode=AutomationMode.AUTO,
                )

                assert run is not None
                assert run.portal == "linkedin"

    @pytest.mark.asyncio
    async def test_run_application_review_mode(self, runner):
        """Test that REVIEW_BEFORE_SUBMIT mode waits for approval"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch(
                "app.services.automation.runner.AdapterFactory"
            ) as mock_factory_cls:
                mock_adapter = AsyncMock()
                mock_adapter.open_job.return_value = {"title": "Test Job"}
                mock_adapter.start_application.return_value = {"status": "started"}
                mock_adapter.fill_application.return_value = {"status": "filled"}
                mock_factory_cls.create.return_value = mock_adapter

                # Mock the job query
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = MagicMock(
                    id=1, url="http://example.com/job"
                )
                mock_session.execute.return_value = mock_result

                run = await runner.run_application(
                    user_id=1,
                    job_id=1,
                    portal="linkedin",
                    mode=AutomationMode.REVIEW_BEFORE_SUBMIT,
                )

                assert run is not None
                assert run.status == AutomationStatus.WAITING_APPROVAL

    @pytest.mark.asyncio
    async def test_approve_run_success(self, runner):
        """Test approving a pending run"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_run = MagicMock()
            mock_run.status = AutomationStatus.WAITING_APPROVAL
            mock_run.run_id = str(uuid.uuid4())

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_run
            mock_session.execute.return_value = mock_result

            result = await runner.approve_run(
                run_id=mock_run.run_id,
                user_id=1,
                approve=True,
                notes="Looks good",
            )

            assert result.status == AutomationStatus.RUNNING

    @pytest.mark.asyncio
    async def test_approve_run_reject(self, runner):
        """Test rejecting a pending run"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_run = MagicMock()
            mock_run.status = AutomationStatus.WAITING_APPROVAL
            mock_run.run_id = str(uuid.uuid4())

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_run
            mock_session.execute.return_value = mock_result

            result = await runner.approve_run(
                run_id=mock_run.run_id,
                user_id=1,
                approve=False,
                notes="Not ready",
            )

            assert result.status == AutomationStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_run_success(self, runner):
        """Test cancelling a running run"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_run = MagicMock()
            mock_run.status = AutomationStatus.RUNNING
            mock_run.run_id = str(uuid.uuid4())

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_run
            mock_session.execute.return_value = mock_result

            result = await runner.cancel_run(
                run_id=mock_run.run_id,
                user_id=1,
            )

            assert result.status == AutomationStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_run_invalid_status(self, runner):
        """Test that cancelling a completed run raises error"""
        with patch(
            "app.services.automation.runner.async_session_factory"
        ) as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            mock_run = MagicMock()
            mock_run.status = AutomationStatus.SUCCESS
            mock_run.run_id = str(uuid.uuid4())

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_run
            mock_session.execute.return_value = mock_result

            with pytest.raises(ValueError, match="cannot be cancelled"):
                await runner.cancel_run(
                    run_id=mock_run.run_id,
                    user_id=1,
                )

    def test_normalize_jobs(self, runner):
        """Test job normalization"""
        jobs = [
            {
                "title": " Python Developer ",
                "company": " Test Co ",
                "location": " NYC ",
                "url": "http://example.com/job",
                "description": "Test description",
            }
        ]

        normalized = runner._normalize_jobs(jobs, "linkedin")

        assert len(normalized) == 1
        assert normalized[0]["title"] == "Python Developer"
        assert normalized[0]["company"] == "Test Co"
        assert normalized[0]["location"] == "NYC"
        assert normalized[0]["source"] == "linkedin"

    def test_analyze_job(self, runner):
        """Test job analysis"""
        job_details = {
            "title": "Python Developer",
            "company": "Test Co",
            "required_skills": ["python", "django"],
        }

        analysis = runner._analyze_job(job_details)

        assert analysis["title"] == "Python Developer"
        assert analysis["company"] == "Test Co"
        assert "required_skills" in analysis
