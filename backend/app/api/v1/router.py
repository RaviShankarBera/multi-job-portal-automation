from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.profile import router as profile_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.recruiters import router as recruiters_router
from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.automation import router as automation_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.scheduled_searches import router as scheduled_searches_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(profile_router, prefix="/profile", tags=["profiles"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_router.include_router(recruiters_router, prefix="/recruiters", tags=["recruiters"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(automation_router, prefix="/automation", tags=["automation"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(scheduled_searches_router, prefix="/scheduled-searches", tags=["scheduled-searches"])
