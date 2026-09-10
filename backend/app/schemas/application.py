from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


VALID_STATUSES = [
    "saved",
    "interested",
    "resume_tailored",
    "ready_to_apply",
    "applied",
    "application_submitted",
    "hr_viewed",
    "recruiter_contacted",
    "interview",
    "technical_round",
    "hr_round",
    "offer",
    "rejected",
    "withdrawn",
    "on_hold",
]

STATUS_PIPELINE = {
    "saved": ["interested", "withdrawn"],
    "interested": ["resume_tailored", "saved", "withdrawn"],
    "resume_tailored": ["ready_to_apply", "interested", "withdrawn"],
    "ready_to_apply": ["applied", "resume_tailored", "withdrawn"],
    "applied": ["application_submitted", "ready_to_apply", "withdrawn"],
    "application_submitted": ["hr_viewed", "recruiter_contacted", "rejected", "withdrawn", "on_hold"],
    "hr_viewed": ["recruiter_contacted", "rejected", "withdrawn", "on_hold"],
    "recruiter_contacted": ["interview", "rejected", "withdrawn", "on_hold"],
    "interview": ["technical_round", "hr_round", "offer", "rejected", "withdrawn", "on_hold"],
    "technical_round": ["hr_round", "offer", "rejected", "withdrawn", "on_hold"],
    "hr_round": ["offer", "rejected", "withdrawn", "on_hold"],
    "offer": ["withdrawn"],
    "rejected": [],
    "withdrawn": [],
    "on_hold": ["applied", "interview", "technical_round", "hr_round", "rejected", "withdrawn"],
}


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    notes: Optional[str] = None
    source: str = "manual"
    automation_mode: str = "manual"


class ApplicationUpdate(BaseModel):
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    automation_mode: Optional[str] = None
    submission_url: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None
    interview_date: Optional[datetime] = None
    salary_offered: Optional[float] = None
    offer_details: Optional[dict] = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class ApplicationSubmitData(BaseModel):
    submission_url: Optional[str] = None
    notes: Optional[str] = None


class ApplicationNoteCreate(BaseModel):
    note: str


class ApplicationFollowUpUpdate(BaseModel):
    follow_up_date: datetime


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    status: str
    applied_date: Optional[datetime] = None
    submission_url: Optional[str] = None
    source: str
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None
    next_follow_up: Optional[datetime] = None
    salary_offered: Optional[float] = None
    offer_details: Optional[dict] = None
    automation_mode: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApplicationEventResponse(BaseModel):
    id: int
    application_id: int
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruiterCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class RecruiterUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class RecruiterResponse(BaseModel):
    id: int
    user_id: int
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    role: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommunicationCreate(BaseModel):
    application_id: Optional[int] = None
    type: str
    direction: str
    subject: Optional[str] = None
    content: str
    communication_date: Optional[datetime] = None


class CommunicationResponse(BaseModel):
    id: int
    recruiter_id: int
    application_id: Optional[int] = None
    type: str
    direction: str
    subject: Optional[str] = None
    content: str
    communication_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsResponse(BaseModel):
    total_applications: int
    by_status: dict
    conversion_rates: dict
    applications_this_week: int
    applications_this_month: int


class PipelineResponse(BaseModel):
    pipeline: dict
    total: int


class FollowUpResponse(BaseModel):
    applications: List[ApplicationResponse]
    total: int
