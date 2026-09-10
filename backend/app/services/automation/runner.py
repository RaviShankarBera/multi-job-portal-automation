import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.automation import AutomationRun, AutomationStep
from app.models.job import Job
from app.models.application import Application
from app.services.automation import AutomationMode, AutomationStatus
from app.services.automation.factory import AdapterFactory
from app.services.automation.monitor import AutomationMonitor

logger = logging.getLogger(__name__)


class AutomationRunner:
    """Orchestrates automation workflows for job searching and applying"""

    def __init__(self):
        self._running_runs: Dict[str, bool] = {}

    async def run_search(
        self,
        user_id: int,
        portal: str,
        params: Dict[str, Any],
        max_retries: int = 3,
    ) -> AutomationRun:
        """
        Execute a job search automation.

        Steps: initialize -> search -> extract -> normalize -> save -> complete
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        async with async_session_factory() as session:
            run = AutomationRun(
                user_id=user_id,
                run_id=run_id,
                portal=portal,
                mode=AutomationMode.AUTO,
                status=AutomationStatus.RUNNING,
                started_at=started_at,
                max_retries=max_retries,
                steps=[],
                errors=[],
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)

            monitor = AutomationMonitor(run_id, user_id)
            adapter = None

            try:
                # Step 1: Initialize
                monitor.start_step("initialize", 1)
                adapter = AdapterFactory.create(portal)
                monitor.complete_step({"adapter": portal})

                # Step 2: Search
                monitor.start_step("search", 2)
                jobs = await adapter.search_jobs(params)
                monitor.complete_step({"jobs_found": len(jobs)})

                # Step 3: Extract (normalize data)
                monitor.start_step("normalize", 3)
                normalized_jobs = self._normalize_jobs(jobs, portal)
                monitor.complete_step({"normalized": len(normalized_jobs)})

                # Step 4: Save to database
                monitor.start_step("save", 4)
                saved_count = await self._save_jobs(session, normalized_jobs, user_id)
                monitor.complete_step({"saved": saved_count})

                # Step 5: Complete
                monitor.start_step("complete", 5)
                run.status = AutomationStatus.SUCCESS
                run.completed_at = datetime.utcnow()
                run.steps = monitor.get_steps_for_storage()
                run.errors = monitor.get_errors_for_storage()
                run.result = {
                    "jobs_found": len(jobs),
                    "jobs_saved": saved_count,
                    "portal": portal,
                }
                await session.commit()

                monitor.complete_step(run.result)

                logger.info(f"[Runner] Search run {run_id} completed successfully")
                return run

            except Exception as e:
                logger.error(f"[Runner] Search run {run_id} failed: {e}")
                run.status = AutomationStatus.FAILED
                run.completed_at = datetime.utcnow()
                run.steps = monitor.get_steps_for_storage()
                run.errors = monitor.get_errors_for_storage()
                run.result = {"error": str(e)}
                await session.commit()

                # Attempt retry if retries remaining
                if run.retry_count < run.max_retries:
                    return await self._retry_run(run, "search", user_id, portal, params)

                return run

            finally:
                if adapter:
                    await adapter.close()
                self._running_runs.pop(run_id, None)

    async def run_application(
        self,
        user_id: int,
        job_id: int,
        portal: str,
        mode: str = AutomationMode.AUTO,
        max_retries: int = 3,
    ) -> AutomationRun:
        """
        Execute an application automation.

        Steps: initialize -> open_job -> analyze -> prepare_resume -> prepare_cover_letter
               -> fill_form -> [approval if REVIEW_BEFORE_SUBMIT] -> submit -> capture -> complete
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        async with async_session_factory() as session:
            run = AutomationRun(
                user_id=user_id,
                run_id=run_id,
                job_id=job_id,
                portal=portal,
                mode=mode,
                status=AutomationStatus.RUNNING,
                started_at=started_at,
                max_retries=max_retries,
                steps=[],
                errors=[],
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)

            monitor = AutomationMonitor(run_id, user_id)
            adapter = None

            try:
                # Step 1: Initialize
                monitor.start_step("initialize", 1)
                adapter = AdapterFactory.create(portal)
                monitor.complete_step({"adapter": portal, "mode": mode})

                # Step 2: Get job details
                monitor.start_step("open_job", 2)
                job = await session.get(Job, job_id)
                if not job:
                    raise ValueError(f"Job {job_id} not found")
                job_details = await adapter.open_job(job.url or job.application_url)
                monitor.complete_step(job_details)

                # Step 3: Analyze job
                monitor.start_step("analyze", 3)
                analysis = self._analyze_job(job_details)
                monitor.complete_step(analysis)

                # Step 4: Prepare resume
                monitor.start_step("prepare_resume", 4)
                resume_path = await self._prepare_resume(user_id, job_id, session)
                monitor.complete_step({"resume_path": resume_path})

                # Step 5: Prepare cover letter
                monitor.start_step("prepare_cover_letter", 5)
                cover_letter = await self._prepare_cover_letter(user_id, job_id, session)
                monitor.complete_step({"has_cover_letter": cover_letter is not None})

                # Step 6: Start application
                monitor.start_step("start_application", 6)
                app_result = await adapter.start_application(
                    job.url or job.application_url
                )
                monitor.complete_step(app_result)

                # Step 7: Fill form
                monitor.start_step("fill_form", 7)
                application_data = {
                    "resume_path": resume_path,
                    "cover_letter": cover_letter,
                    **analysis.get("suggested_fields", {}),
                }
                fill_result = await adapter.fill_application(application_data)
                monitor.complete_step(fill_result)

                # Upload resume if path provided
                if resume_path:
                    await adapter.upload_resume(resume_path)

                # Step 8: Approval (if REVIEW_BEFORE_SUBMIT mode)
                if mode == AutomationMode.REVIEW_BEFORE_SUBMIT:
                    monitor.start_step("awaiting_approval", 8)
                    run.status = AutomationStatus.WAITING_APPROVAL
                    run.steps = monitor.get_steps_for_storage()
                    await session.commit()
                    monitor.complete_step({"status": "waiting_approval"})

                    logger.info(
                        f"[Runner] Run {run_id} waiting for approval"
                    )
                    return run

                # Step 9: Submit
                monitor.start_step("submit", 9)
                submit_result = await adapter.submit_application()
                monitor.complete_step(submit_result)

                # Step 10: Capture confirmation
                monitor.start_step("capture_confirmation", 10)
                confirmation = await adapter.capture_confirmation()
                monitor.complete_step(confirmation)

                # Step 11: Complete
                monitor.start_step("complete", 11)

                # Create application record
                application = Application(
                    user_id=user_id,
                    job_id=job_id,
                    status="applied",
                    applied_date=datetime.utcnow(),
                    source=portal,
                    submission_url=job.url,
                    automation_mode=mode,
                )
                session.add(application)
                await session.commit()
                await session.refresh(application)

                run.application_id = application.id
                run.status = AutomationStatus.SUCCESS
                run.completed_at = datetime.utcnow()
                run.steps = monitor.get_steps_for_storage()
                run.errors = monitor.get_errors_for_storage()
                run.result = {
                    "application_id": application.id,
                    "confirmation": confirmation,
                    "portal": portal,
                }
                await session.commit()

                monitor.complete_step(run.result)

                logger.info(f"[Runner] Application run {run_id} completed successfully")
                return run

            except Exception as e:
                logger.error(f"[Runner] Application run {run_id} failed: {e}")

                # Capture screenshot on failure
                if adapter and adapter.page:
                    screenshot_path = await monitor.capture_screenshot(
                        adapter.page, "failure"
                    )
                    run.screenshot_path = screenshot_path

                run.status = AutomationStatus.FAILED
                run.completed_at = datetime.utcnow()
                run.steps = monitor.get_steps_for_storage()
                run.errors = monitor.get_errors_for_storage()
                run.result = {"error": str(e)}
                await session.commit()

                # Attempt retry if retries remaining
                if run.retry_count < run.max_retries:
                    return await self._retry_run(
                        run, "application", user_id, portal,
                        {"job_id": job_id, "mode": mode}
                    )

                return run

            finally:
                if adapter:
                    await adapter.close()
                self._running_runs.pop(run_id, None)

    async def approve_run(
        self,
        run_id: str,
        user_id: int,
        approve: bool,
        notes: Optional[str] = None,
    ) -> AutomationRun:
        """Approve or reject a pending automation run"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(AutomationRun).where(
                    AutomationRun.run_id == run_id,
                    AutomationRun.user_id == user_id,
                )
            )
            run = result.scalar_one_or_none()

            if not run:
                raise ValueError(f"Run {run_id} not found")

            if run.status != AutomationStatus.WAITING_APPROVAL:
                raise ValueError(
                    f"Run {run_id} is not awaiting approval (status: {run.status})"
                )

            if approve:
                # Resume the application process
                run.status = AutomationStatus.RUNNING
                run.steps = run.steps or []
                run.steps.append({
                    "step_name": "approval_granted",
                    "status": "completed",
                    "data": {"approved": True, "notes": notes},
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await session.commit()

                # Continue the application process
                # In production, this would be handled by a background worker
                logger.info(f"[Runner] Run {run_id} approved, continuing...")
            else:
                run.status = AutomationStatus.CANCELLED
                run.completed_at = datetime.utcnow()
                run.steps = run.steps or []
                run.steps.append({
                    "step_name": "approval_rejected",
                    "status": "completed",
                    "data": {"approved": False, "notes": notes},
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await session.commit()

                logger.info(f"[Runner] Run {run_id} rejected")

            return run

    async def cancel_run(self, run_id: str, user_id: int) -> AutomationRun:
        """Cancel a running automation"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(AutomationRun).where(
                    AutomationRun.run_id == run_id,
                    AutomationRun.user_id == user_id,
                )
            )
            run = result.scalar_one_or_none()

            if not run:
                raise ValueError(f"Run {run_id} not found")

            if run.status not in [
                AutomationStatus.RUNNING,
                AutomationStatus.WAITING_APPROVAL,
                AutomationStatus.RETRYING,
            ]:
                raise ValueError(
                    f"Run {run_id} cannot be cancelled (status: {run.status})"
                )

            run.status = AutomationStatus.CANCELLED
            run.completed_at = datetime.utcnow()
            run.steps = run.steps or []
            run.steps.append({
                "step_name": "cancelled",
                "status": "completed",
                "data": {"cancelled_at": datetime.utcnow().isoformat()},
                "timestamp": datetime.utcnow().isoformat(),
            })
            await session.commit()

            self._running_runs.pop(run_id, None)
            logger.info(f"[Runner] Run {run_id} cancelled")

            return run

    async def get_run(self, run_id: str, user_id: int) -> Optional[AutomationRun]:
        """Get a specific automation run"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(AutomationRun).where(
                    AutomationRun.run_id == run_id,
                    AutomationRun.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()

    async def list_runs(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        portal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List automation runs for a user"""
        async with async_session_factory() as session:
            query = select(AutomationRun).where(AutomationRun.user_id == user_id)

            if status:
                query = query.where(AutomationRun.status == status)
            if portal:
                query = query.where(AutomationRun.portal == portal)

            query = query.order_by(AutomationRun.created_at.desc())

            # Count total
            count_query = select(AutomationRun).where(AutomationRun.user_id == user_id)
            if status:
                count_query = count_query.where(AutomationRun.status == status)
            if portal:
                count_query = count_query.where(AutomationRun.portal == portal)

            total_result = await session.execute(count_query)
            total = len(total_result.scalars().all())

            # Paginate
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            result = await session.execute(query)
            runs = result.scalars().all()

            return {
                "runs": runs,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }

    def _normalize_jobs(self, jobs: List[Dict], portal: str) -> List[Dict]:
        """Normalize job data to consistent format"""
        normalized = []
        for job in jobs:
            normalized.append({
                "source": portal,
                "title": job.get("title", "Unknown"),
                "company": job.get("company", "Unknown"),
                "location": job.get("location", "Unknown"),
                "url": job.get("url"),
                "description": job.get("description", job.get("snippet", "")),
                "remote_status": job.get("remote_status"),
                "employment_type": job.get("employment_type", "full-time"),
            })
        return normalized

    async def _save_jobs(
        self, session: AsyncSession, jobs: List[Dict], user_id: int
    ) -> int:
        """Save normalized jobs to database, avoiding duplicates"""
        saved_count = 0
        for job_data in jobs:
            # Check for duplicate by URL
            if job_data.get("url"):
                existing = await session.execute(
                    select(Job).where(Job.url == job_data["url"])
                )
                if existing.scalar_one_or_none():
                    continue

            job = Job(
                source=job_data["source"],
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                url=job_data.get("url"),
                description=job_data.get("description"),
                remote_status=job_data.get("remote_status"),
                employment_type=job_data.get("employment_type", "full-time"),
            )
            session.add(job)
            saved_count += 1

        await session.commit()
        return saved_count

    def _analyze_job(self, job_details: Dict) -> Dict:
        """Analyze job details for application preparation"""
        return {
            "title": job_details.get("title", ""),
            "company": job_details.get("company", ""),
            "required_skills": job_details.get("required_skills", []),
            "suggested_fields": {},
        }

    async def _prepare_resume(
        self, user_id: int, job_id: int, session: AsyncSession
    ) -> Optional[str]:
        """Prepare resume for application"""
        # In production, this would use the AI resume tailoring service
        # For now, return None to indicate no resume prepared
        return None

    async def _prepare_cover_letter(
        self, user_id: int, job_id: int, session: AsyncSession
    ) -> Optional[str]:
        """Prepare cover letter for application"""
        # In production, this would use the AI cover letter service
        return None

    async def _retry_run(
        self,
        run: AutomationRun,
        run_type: str,
        user_id: int,
        portal: str,
        params: Dict[str, Any],
    ) -> AutomationRun:
        """Retry a failed automation run"""
        async with async_session_factory() as session:
            run.retry_count += 1
            run.status = AutomationStatus.RETRYING
            run.steps = run.steps or []
            run.steps.append({
                "step_name": "retry",
                "status": "running",
                "data": {
                    "attempt": run.retry_count,
                    "max_retries": run.max_retries,
                },
                "timestamp": datetime.utcnow().isoformat(),
            })
            await session.commit()

            logger.info(
                f"[Runner] Retrying run {run.run_id} "
                f"(attempt {run.retry_count}/{run.max_retries})"
            )

            # In production, this would schedule a background task
            # For now, we return the run in retrying status
            return run
