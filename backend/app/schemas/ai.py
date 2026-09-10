from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(..., min_length=10, max_length=50000)


class JobAnalysisResponse(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_years: Optional[int] = None
    responsibilities: List[str] = []
    qualifications: List[str] = []
    salary_range: Optional[Dict[str, Any]] = None
    remote_status: Optional[str] = None
    employment_type: str = "full-time"
    industry: Optional[str] = None
    key_requirements: Optional[str] = None


class TailorResumeRequest(BaseModel):
    resume_id: int
    job_id: int


class ChangeItem(BaseModel):
    section: str
    description: str


class OriginalVsTailored(BaseModel):
    original_ats_score: Optional[float] = None
    tailored_ats_score: Optional[float] = None
    keyword_improvement: Optional[str] = None


class TailoredResumeResponse(BaseModel):
    version_id: int
    tailored_content: Dict[str, Any]
    original_ats_score: Optional[float] = None
    tailored_ats_score: Optional[float] = None
    changes_made: List[ChangeItem] = []
    original_vs_tailored: Optional[OriginalVsTailored] = None


class CoverLetterRequest(BaseModel):
    resume_id: int
    job_id: int


class CoverLetterRegenerateRequest(BaseModel):
    job_id: int
    feedback: str = Field(..., min_length=5, max_length=5000)


class CoverLetterResponse(BaseModel):
    cover_letter: str
    job_id: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SkillGapRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=200)


class LearningRecommendation(BaseModel):
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    estimated_time: Optional[str] = None
    difficulty_level: Optional[str] = None


class PrioritySkill(BaseModel):
    skill: str
    reason: Optional[str] = None


class SkillGapResponse(BaseModel):
    target_role: str
    strong_skills: List[str] = []
    missing_skills: List[str] = []
    overlapping_skills: List[str] = []
    priority_skills: List[PrioritySkill] = []
    learning_recommendations: Dict[str, LearningRecommendation] = {}
    overall_gap_score: Optional[float] = None
    summary: Optional[str] = None
    user_skills_count: int = 0
    market_skills_count: int = 0


class InterviewQuestionsRequest(BaseModel):
    job_id: int
    resume_id: int


class InterviewQuestionItem(BaseModel):
    question: str
    category: str
    difficulty: str
    tips: Optional[str] = None
    suggested_answer_points: List[str] = []


class InterviewQuestionsResponse(BaseModel):
    questions: List[InterviewQuestionItem]
    job_id: int
    resume_id: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ApplicationAnswersRequest(BaseModel):
    job_id: int
    questions: List[str] = Field(..., min_length=1, max_length=20)


class ApplicationAnswersResponse(BaseModel):
    answers: Dict[str, str]
    job_id: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractKeywordsRequest(BaseModel):
    job_description: str = Field(..., min_length=10, max_length=50000)


class ExtractKeywordsResponse(BaseModel):
    keywords: List[str]
    count: int


class CompanyAnalysisRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)


class CompanyAnalysisResponse(BaseModel):
    overview: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    founded: Optional[str] = None
    headquarters: Optional[str] = None
    culture: Optional[str] = None
    benefits: Optional[List[str]] = None
    recent_news: Optional[str] = None
    glassdoor_rating: Optional[str] = None
