from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class AutomationStartRequest(BaseModel):
    job_id: Optional[int] = None
    portal: str = Field(..., min_length=1, max_length=50)
    mode: str = Field(default="auto", pattern="^(auto|review_before_submit|manual)$")
    job_url: Optional[str] = None
    search_params: Optional[dict] = None


class AutomationStepResult(BaseModel):
    step_name: str
    step_order: int
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AutomationApprovalRequest(BaseModel):
    approve: bool
    notes: Optional[str] = None


class AutomationRunResponse(BaseModel):
    id: int
    user_id: int
    run_id: str
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    portal: str
    mode: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[AutomationStepResult] = []
    errors: List[dict] = []
    retry_count: int = 0
    max_retries: int = 3
    screenshot_path: Optional[str] = None
    result: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutomationRunListResponse(BaseModel):
    runs: List[AutomationRunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AutomationRetryRequest(BaseModel):
    notes: Optional[str] = None
