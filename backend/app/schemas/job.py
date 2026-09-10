from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    source: str = "manual"
    source_id: Optional[str] = None
    url: Optional[str] = None
    title: str
    company: str
    location: str
    remote_status: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    experience_years: Optional[int] = None
    employment_type: str = "full-time"
    description: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    qualifications: List[str] = []
    posted_date: Optional[datetime] = None
    application_url: Optional[str] = None
    status: str = "new"


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    remote_status: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    experience_years: Optional[int] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    posted_date: Optional[datetime] = None
    application_url: Optional[str] = None
    status: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    source: str
    source_id: Optional[str] = None
    url: Optional[str] = None
    title: str
    company: str
    location: str
    remote_status: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str
    experience_years: Optional[int] = None
    employment_type: str
    description: Optional[str] = None
    required_skills: List[Any] = []
    preferred_skills: List[Any] = []
    responsibilities: List[Any] = []
    qualifications: List[Any] = []
    posted_date: Optional[datetime] = None
    collected_date: datetime
    application_url: Optional[str] = None
    status: str
    duplicate_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobSearchParams(BaseModel):
    keywords: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    industry: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[List[str]] = None
    employment_type: Optional[str] = None
    date_posted: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    page: int = 1
    page_size: int = 20


class JobMatchResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    overall_score: float
    skills_score: float
    experience_score: float
    title_score: float
    industry_score: float
    location_score: float
    salary_score: float
    education_score: float
    certification_score: float
    explanation: Optional[str] = None
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedJobCreate(BaseModel):
    notes: Optional[str] = None
    user_notes: Optional[str] = None


class SavedJobResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    notes: Optional[str] = None
    user_notes: Optional[str] = None
    saved_at: datetime
    job: JobResponse

    model_config = ConfigDict(from_attributes=True)


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool
    existing_job_id: Optional[int] = None
    hash_value: str


class JobStatsResponse(BaseModel):
    total_jobs: int
    jobs_by_source: dict
    jobs_by_status: dict
    saved_jobs_count: int
    matched_jobs_count: int
    average_match_score: Optional[float] = None
