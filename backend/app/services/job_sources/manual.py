from datetime import datetime
from typing import List, Optional

from app.services.job_sources import JobSourceAdapter


class ManualJobAdapter(JobSourceAdapter):
    """Adapter for manually entered jobs by users"""

    def __init__(self):
        super().__init__(source_name="manual")

    async def search_jobs(self, params: dict) -> List[dict]:
        return []

    async def get_job_details(self, job_id: str) -> Optional[dict]:
        return None

    def normalize_job(self, raw_job: dict) -> dict:
        normalized = super().normalize_job(raw_job)
        normalized["source"] = "manual"
        normalized["collected_date"] = datetime.utcnow()

        title = normalized.get("title", "").strip()
        company = normalized.get("company", "").strip()
        location = normalized.get("location", "").strip()

        if not title:
            raise ValueError("Job title is required")
        if not company:
            raise ValueError("Company name is required")
        if not location:
            raise ValueError("Job location is required")

        employment_type = normalized.get("employment_type", "full-time")
        valid_types = ["full-time", "part-time", "contract", "internship", "freelance"]
        if employment_type not in valid_types:
            normalized["employment_type"] = "full-time"

        remote_status = normalized.get("remote_status")
        valid_remote = ["remote", "hybrid", "onsite"]
        if remote_status and remote_status not in valid_remote:
            normalized["remote_status"] = None

        salary_min = normalized.get("salary_min")
        salary_max = normalized.get("salary_max")
        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                normalized["salary_min"] = salary_max
                normalized["salary_max"] = salary_min

        return normalized

    def create_manual_job(
        self,
        title: str,
        company: str,
        location: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        application_url: Optional[str] = None,
        remote_status: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        employment_type: str = "full-time",
        experience_years: Optional[int] = None,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
    ) -> dict:
        raw_job = {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "url": url,
            "application_url": application_url,
            "remote_status": remote_status,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "employment_type": employment_type,
            "experience_years": experience_years,
            "required_skills": required_skills or [],
            "preferred_skills": preferred_skills or [],
        }
        return self.normalize_job(raw_job)
