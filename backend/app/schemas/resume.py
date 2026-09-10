from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class ResumeBase(BaseModel):
    title: str
    tags: Optional[List[str]] = None


class ResumeCreate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class ResumeResponse(ResumeBase):
    id: int
    user_id: int
    original_filename: str
    file_size: int
    file_type: str
    is_primary: bool
    parsed_content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int


class ResumeVersionCreate(BaseModel):
    job_id: Optional[int] = None
    tailored_content: Optional[Dict[str, Any]] = None


class ResumeVersionResponse(BaseModel):
    id: int
    resume_id: int
    version_number: int
    tailored_content: Optional[Dict[str, Any]] = None
    job_id: Optional[int] = None
    ats_score: Optional[float] = None
    file_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeParseResult(BaseModel):
    contact_info: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Dict[str, Any]]] = None


class ATSScoreResponse(BaseModel):
    ats_score: float
    keyword_match: float
    missing_keywords: List[str]
    suggestions: List[str]
    sections_present: Dict[str, bool]
