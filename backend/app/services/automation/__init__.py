from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AutomationMode(str, Enum):
    AUTO = "auto"
    REVIEW_BEFORE_SUBMIT = "review_before_submit"
    MANUAL = "manual"


class AutomationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPortalAdapter(ABC):
    """Abstract base class for job portal automation adapters"""

    @abstractmethod
    async def search_jobs(self, params: Dict[str, Any]) -> List[Dict]:
        """Search for jobs on the portal"""
        pass

    @abstractmethod
    async def open_job(self, job_url: str) -> Dict:
        """Open and extract job details"""
        pass

    @abstractmethod
    async def extract_job(self, page) -> Dict:
        """Extract job information from current page"""
        pass

    @abstractmethod
    async def start_application(self, job_url: str) -> Dict:
        """Start the application process"""
        pass

    @abstractmethod
    async def fill_application(self, application_data: Dict) -> Dict:
        """Fill application form fields"""
        pass

    @abstractmethod
    async def upload_resume(self, file_path: str) -> bool:
        """Upload resume to the application"""
        pass

    @abstractmethod
    async def submit_application(self) -> Dict:
        """Submit the application"""
        pass

    @abstractmethod
    async def capture_confirmation(self) -> Dict:
        """Capture submission confirmation"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close browser resources"""
        pass
