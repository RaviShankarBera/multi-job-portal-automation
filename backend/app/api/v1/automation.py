import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.automation import (
    AutomationStartRequest,
    AutomationRunResponse,
    AutomationRunListResponse,
    AutomationApprovalRequest,
    AutomationRetryRequest,
)
from app.services.automation.runner import AutomationRunner

logger = logging.getLogger(__name__)

router = APIRouter()
runner = AutomationRunner()


@router.post("/search", response_model=AutomationRunResponse)
async def start_job_search(
    request: AutomationStartRequest,
    current_user: User = Depends(get_current_user),
):
    """Start a job search automation run"""
    try:
        if not request.search_params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="search_params is required for search automation",
            )

        run = await runner.run_search(
            user_id=current_user.id,
            portal=request.portal,
            params=request.search_params,
        )

        return AutomationRunResponse.model_validate(run)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start search automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start search automation",
        )


@router.post("/apply", response_model=AutomationRunResponse)
async def start_application(
    request: AutomationStartRequest,
    current_user: User = Depends(get_current_user),
):
    """Start an application automation run"""
    try:
        if not request.job_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_id is required for application automation",
            )

        run = await runner.run_application(
            user_id=current_user.id,
            job_id=request.job_id,
            portal=request.portal,
            mode=request.mode,
        )

        return AutomationRunResponse.model_validate(run)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start application automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start application automation",
        )


@router.get("/runs", response_model=AutomationRunListResponse)
async def list_automation_runs(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    portal: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List automation runs for the current user"""
    try:
        result = await runner.list_runs(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            status=status,
            portal=portal,
        )

        runs = [AutomationRunResponse.model_validate(run) for run in result["runs"]]

        return AutomationRunListResponse(
            runs=runs,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )

    except Exception as e:
        logger.error(f"Failed to list automation runs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list automation runs",
        )


@router.get("/runs/{run_id}", response_model=AutomationRunResponse)
async def get_automation_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific automation run"""
    try:
        run = await runner.get_run(run_id, current_user.id)

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found",
            )

        return AutomationRunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get automation run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get automation run",
        )


@router.post("/runs/{run_id}/approve", response_model=AutomationRunResponse)
async def approve_automation_run(
    run_id: str,
    request: AutomationApprovalRequest,
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a pending automation run"""
    try:
        run = await runner.approve_run(
            run_id=run_id,
            user_id=current_user.id,
            approve=request.approve,
            notes=request.notes,
        )

        return AutomationRunResponse.model_validate(run)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to approve automation run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve automation run",
        )


@router.post("/runs/{run_id}/retry", response_model=AutomationRunResponse)
async def retry_automation_run(
    run_id: str,
    request: AutomationRetryRequest,
    current_user: User = Depends(get_current_user),
):
    """Retry a failed automation run"""
    try:
        run = await runner.get_run(run_id, current_user.id)

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found",
            )

        if run.status not in ["failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run {run_id} cannot be retried (status: {run.status})",
            )

        # Create a new run with the same parameters
        from app.services.automation import AutomationMode

        if run.job_id:
            new_run = await runner.run_application(
                user_id=current_user.id,
                job_id=run.job_id,
                portal=run.portal,
                mode=run.mode,
            )
        else:
            # For search runs, we'd need to store search params
            # For now, raise an error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retry search runs without stored parameters",
            )

        return AutomationRunResponse.model_validate(new_run)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry automation run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry automation run",
        )


@router.delete("/runs/{run_id}/cancel", response_model=AutomationRunResponse)
async def cancel_automation_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a running automation"""
    try:
        run = await runner.cancel_run(run_id, current_user.id)
        return AutomationRunResponse.model_validate(run)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to cancel automation run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel automation run",
        )
