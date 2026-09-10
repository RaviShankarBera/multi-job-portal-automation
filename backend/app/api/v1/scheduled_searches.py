from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.scheduled_search import ScheduledSearchService
from app.schemas.scheduled_search import (
    ScheduledSearchCreate,
    ScheduledSearchUpdate,
    ScheduledSearchResponse,
    ScheduledSearchListResponse,
    ScheduledSearchExecutionResponse
)

router = APIRouter(prefix="/scheduled-searches", tags=["scheduled-searches"])


@router.post("", response_model=ScheduledSearchResponse, status_code=201)
async def create_scheduled_search(
    search_data: ScheduledSearchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new scheduled search."""
    scheduled_search_service = ScheduledSearchService(db)
    
    scheduled_search = await scheduled_search_service.create_scheduled_search(
        user_id=current_user.id,
        data=search_data.model_dump()
    )
    
    return ScheduledSearchResponse.model_validate(scheduled_search)


@router.get("", response_model=ScheduledSearchListResponse)
async def list_scheduled_searches(
    include_inactive: bool = Query(False, description="Include inactive searches"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all scheduled searches for the current user."""
    scheduled_search_service = ScheduledSearchService(db)
    
    scheduled_searches = await scheduled_search_service.get_user_scheduled_searches(
        user_id=current_user.id,
        include_inactive=include_inactive
    )
    
    return ScheduledSearchListResponse(
        scheduled_searches=[ScheduledSearchResponse.model_validate(s) for s in scheduled_searches],
        total=len(scheduled_searches)
    )


@router.get("/{search_id}", response_model=ScheduledSearchResponse)
async def get_scheduled_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scheduled search."""
    scheduled_search_service = ScheduledSearchService(db)
    
    scheduled_search = await scheduled_search_service.get_scheduled_search_by_id(
        search_id=search_id,
        user_id=current_user.id
    )
    
    return ScheduledSearchResponse.model_validate(scheduled_search)


@router.put("/{search_id}", response_model=ScheduledSearchResponse)
async def update_scheduled_search(
    search_id: int,
    search_data: ScheduledSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a scheduled search."""
    scheduled_search_service = ScheduledSearchService(db)
    
    # Filter out None values
    update_data = {k: v for k, v in search_data.model_dump().items() if v is not None}
    
    scheduled_search = await scheduled_search_service.update_scheduled_search(
        search_id=search_id,
        user_id=current_user.id,
        data=update_data
    )
    
    return ScheduledSearchResponse.model_validate(scheduled_search)


@router.delete("/{search_id}")
async def delete_scheduled_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a scheduled search."""
    scheduled_search_service = ScheduledSearchService(db)
    
    success = await scheduled_search_service.delete_scheduled_search(
        search_id=search_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete scheduled search")
    
    return {"message": "Scheduled search deleted successfully"}


@router.post("/{search_id}/run", response_model=ScheduledSearchExecutionResponse)
async def run_scheduled_search_now(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a scheduled search immediately."""
    scheduled_search_service = ScheduledSearchService(db)
    
    # Verify the search belongs to the user
    scheduled_search = await scheduled_search_service.get_scheduled_search_by_id(
        search_id=search_id,
        user_id=current_user.id
    )
    
    # Execute the search
    result = await scheduled_search_service.execute_scheduled_search(search_id)
    
    return ScheduledSearchExecutionResponse(
        search_id=result["search_id"],
        jobs_found=result["jobs_found"],
        high_match_count=result["high_match_count"],
        message=result["message"],
        execution_time=result["execution_time"]
    )
