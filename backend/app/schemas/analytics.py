from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class TopSkillItem(BaseModel):
    skill: str
    count: int
    percentage: float


class ConversionRates(BaseModel):
    application_to_hr: float = 0.0
    hr_to_interview: float = 0.0
    interview_to_offer: float = 0.0


class RecentActivity(BaseModel):
    type: str
    description: str
    timestamp: Optional[datetime] = None


class DashboardSummaryResponse(BaseModel):
    jobs_found_total: int = 0
    jobs_today: int = 0
    jobs_this_week: int = 0
    applications_total: int = 0
    applications_this_week: int = 0
    applications_this_month: int = 0
    interviews_count: int = 0
    offers_count: int = 0
    rejections_count: int = 0
    pending_count: int = 0
    match_rate: float = 0.0
    conversion_rates: ConversionRates = ConversionRates()
    top_skills_demand: List[TopSkillItem] = []
    recent_activity: List[RecentActivity] = []
    recommended_jobs: List[Dict[str, Any]] = []
    application_pipeline: Dict[str, int] = {}
    upcoming_follow_ups: List[Dict[str, Any]] = []


class DailyPerformance(BaseModel):
    date: str
    applications: int = 0
    responses: int = 0
    interviews: int = 0


class WeeklyPerformanceResponse(BaseModel):
    period_start: str
    period_end: str
    daily_data: List[DailyPerformance] = []
    total_applications: int = 0
    total_responses: int = 0
    total_interviews: int = 0


class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float = 0.0


class ApplicationFunnelResponse(BaseModel):
    stages: List[FunnelStage] = []
    total: int = 0
    conversion_rates: Dict[str, float] = {}


class SalaryStats(BaseModel):
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    avg_salary: Optional[float] = None
    median_salary: Optional[float] = None
    sample_size: int = 0


class JobMarketResponse(BaseModel):
    skills_demand: List[TopSkillItem] = []
    top_job_titles: List[Dict[str, Any]] = []
    salary_ranges: Optional[SalaryStats] = None
    companies_hiring: List[Dict[str, Any]] = []
    locations_demand: List[Dict[str, Any]] = []
    remote_percentage: float = 0.0
    technology_trends: Dict[str, Any] = {}
    industry_distribution: List[Dict[str, Any]] = []


class SkillCoverageItem(BaseModel):
    skill: str
    user_has: bool
    market_demand: float
    importance: str = "medium"


class SkillCoverageResponse(BaseModel):
    covered_skills: List[SkillCoverageItem] = []
    missing_skills: List[SkillCoverageItem] = []
    coverage_percentage: float = 0.0
    total_market_skills: int = 0
    user_skills_count: int = 0


class SkillRecommendation(BaseModel):
    skill: str
    demand_score: float
    priority: str
    reason: str
    jobs_requiring: int


class SkillTrendItem(BaseModel):
    skill: str
    direction: str
    change_percentage: float
    current_demand: float


class SkillTrendsResponse(BaseModel):
    trending_up: List[SkillTrendItem] = []
    trending_down: List[SkillTrendItem] = []
    stable: List[SkillTrendItem] = []


class ATSStats(BaseModel):
    average_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    total_resumes: int = 0
    scores_over_time: List[Dict[str, Any]] = []


class ResumePerformanceItem(BaseModel):
    resume_id: int
    title: str
    version_count: int = 0
    average_ats_score: float = 0.0
    applications_count: int = 0
    interview_rate: float = 0.0


class ResumePerformanceResponse(BaseModel):
    ats_scores: ATSStats = ATSStats()
    resume_performance: List[ResumePerformanceItem] = []
    correlation_insight: str = ""


class AnalyticsSnapshotResponse(BaseModel):
    id: int
    user_id: int
    snapshot_type: str
    snapshot_date: date
    data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SnapshotListResponse(BaseModel):
    snapshots: List[AnalyticsSnapshotResponse] = []
    total: int = 0


class CreateSnapshotRequest(BaseModel):
    snapshot_type: str = Field(..., pattern="^(daily|weekly|monthly)$")
