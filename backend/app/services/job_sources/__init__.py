from abc import ABC, abstractmethod
from typing import List, Optional


class JobSourceAdapter(ABC):
    """Base class for job source adapters"""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    async def search_jobs(self, params: dict) -> List[dict]:
        """Search for jobs and return normalized results"""
        pass

    @abstractmethod
    async def get_job_details(self, job_id: str) -> Optional[dict]:
        """Get detailed job information"""
        pass

    def normalize_job(self, raw_job: dict) -> dict:
        """Normalize raw job data to common schema"""
        normalized = {
            "source": self.source_name,
            "source_id": str(raw_job.get("id", "")),
            "url": raw_job.get("url", ""),
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company", ""),
            "location": raw_job.get("location", ""),
            "remote_status": raw_job.get("remote_status"),
            "salary_min": raw_job.get("salary_min"),
            "salary_max": raw_job.get("salary_max"),
            "salary_currency": raw_job.get("salary_currency", "USD"),
            "experience_years": raw_job.get("experience_years"),
            "employment_type": raw_job.get("employment_type", "full-time"),
            "description": raw_job.get("description", ""),
            "required_skills": raw_job.get("required_skills", []),
            "preferred_skills": raw_job.get("preferred_skills", []),
            "responsibilities": raw_job.get("responsibilities", []),
            "qualifications": raw_job.get("qualifications", []),
            "posted_date": raw_job.get("posted_date"),
            "application_url": raw_job.get("application_url"),
        }
        return normalized
