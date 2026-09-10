import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AutomationMonitor:
    """Monitors and logs automation runs with timestamps, screenshots, and reporting"""

    def __init__(self, run_id: str, user_id: int):
        self.run_id = run_id
        self.user_id = user_id
        self.steps: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.current_step: Optional[Dict[str, Any]] = None
        self.step_start_time: Optional[float] = None
        self.screenshot_dir = Path("uploads/automation_screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def start_step(self, step_name: str, step_order: int) -> None:
        """Start tracking a new step"""
        if self.current_step:
            self.complete_step()

        self.step_start_time = time.time()
        self.current_step = {
            "step_name": step_name,
            "step_order": step_order,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "data": None,
            "error": None,
        }
        logger.info(f"[Run {self.run_id}] Starting step: {step_name} (order: {step_order})")

    def complete_step(self, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Complete the current step and return its result"""
        if not self.current_step:
            return {}

        duration_ms = int((time.time() - (self.step_start_time or time.time())) * 1000)
        self.current_step["status"] = "completed"
        self.current_step["completed_at"] = datetime.utcnow().isoformat()
        self.current_step["duration_ms"] = duration_ms
        self.current_step["data"] = data

        step_result = self.current_step.copy()
        self.steps.append(step_result)
        logger.info(
            f"[Run {self.run_id}] Completed step: {step_result['step_name']} "
            f"in {duration_ms}ms"
        )

        self.current_step = None
        self.step_start_time = None
        return step_result

    def fail_step(self, error: str) -> Dict[str, Any]:
        """Mark the current step as failed"""
        if not self.current_step:
            return {}

        duration_ms = int((time.time() - (self.step_start_time or time.time())) * 1000)
        self.current_step["status"] = "failed"
        self.current_step["completed_at"] = datetime.utcnow().isoformat()
        self.current_step["duration_ms"] = duration_ms
        self.current_step["error"] = error

        step_result = self.current_step.copy()
        self.steps.append(step_result)

        error_entry = {
            "step_name": step_result["step_name"],
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
        }
        self.errors.append(error_entry)

        logger.error(
            f"[Run {self.run_id}] Failed step: {step_result['step_name']} - {error}"
        )

        self.current_step = None
        self.step_start_time = None
        return step_result

    async def capture_screenshot(self, page, step_name: str) -> Optional[str]:
        """Capture a screenshot of the current page state"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.run_id}_{step_name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"[Run {self.run_id}] Screenshot captured: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"[Run {self.run_id}] Failed to capture screenshot: {e}")
            return None

    def track_retry(self, attempt: int, max_retries: int, reason: str) -> None:
        """Log a retry attempt"""
        self.errors.append({
            "type": "retry",
            "attempt": attempt,
            "max_retries": max_retries,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.warning(
            f"[Run {self.run_id}] Retry attempt {attempt}/{max_retries}: {reason}"
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report of the run"""
        total_duration_ms = sum(
            step.get("duration_ms", 0) for step in self.steps
        )
        completed_steps = sum(
            1 for step in self.steps if step.get("status") == "completed"
        )
        failed_steps = sum(
            1 for step in self.steps if step.get("status") == "failed"
        )

        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "total_steps": len(self.steps),
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "total_duration_ms": total_duration_ms,
            "total_errors": len(self.errors),
            "steps": self.steps,
            "errors": self.errors,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_steps_for_storage(self) -> List[Dict[str, Any]]:
        """Get steps in a format suitable for database storage"""
        return [
            {
                "step_name": step["step_name"],
                "step_order": step["step_order"],
                "status": step["status"],
                "data": step.get("data"),
                "error": step.get("error"),
                "started_at": step.get("started_at"),
                "completed_at": step.get("completed_at"),
                "duration_ms": step.get("duration_ms"),
            }
            for step in self.steps
        ]

    def get_errors_for_storage(self) -> List[Dict[str, Any]]:
        """Get errors in a format suitable for database storage"""
        return self.errors.copy()
