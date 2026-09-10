from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    target_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[Any]] = None
    technical_skills: Optional[List[Any]] = None
    soft_skills: Optional[List[Any]] = None
    certifications: Optional[List[Any]] = None
    education: Optional[List[Any]] = None
    companies_worked: Optional[List[Any]] = None
    job_history: Optional[List[Any]] = None
    salary_current: Optional[float] = None
    expected_salary: Optional[float] = None
    notice_period: Optional[str] = None
    preferred_locations: Optional[List[Any]] = None
    remote_preference: Optional[str] = None
    preferred_industries: Optional[List[Any]] = None
    preferred_companies: Optional[List[Any]] = None
    target_roles: Optional[List[Any]] = None
    visa_status: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    target_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[Any]] = None
    technical_skills: Optional[List[Any]] = None
    soft_skills: Optional[List[Any]] = None
    certifications: Optional[List[Any]] = None
    education: Optional[List[Any]] = None
    companies_worked: Optional[List[Any]] = None
    job_history: Optional[List[Any]] = None
    salary_current: Optional[float] = None
    expected_salary: Optional[float] = None
    notice_period: Optional[str] = None
    preferred_locations: Optional[List[Any]] = None
    remote_preference: Optional[str] = None
    preferred_industries: Optional[List[Any]] = None
    preferred_companies: Optional[List[Any]] = None
    target_roles: Optional[List[Any]] = None
    visa_status: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillsUpdate(BaseModel):
    skills: List[str]
    technical_skills: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None