from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Annotated
from supabase import Client
from ....core.dependencies import get_current_user_auth0_id, get_db
from ....core.rate_limiting import limiter, API_RATE_LIMIT
from ....schemas.onboarding.progress import (
    OnboardingProgressResponse,
    OnboardingActionRequest,
    OnboardingStatusResponse,
)
from ....services.onboarding.onboarding_progress_service import (
    OnboardingProgressService,
)
from ....core.logging import get_logger
from ....core.exceptions import UserNotFoundError

router = APIRouter(prefix="/progress", tags=["onboarding-progress"])
logger = get_logger(__name__)


@router.get("/status", response_model=OnboardingStatusResponse)
@limiter.limit(API_RATE_LIMIT)
async def get_onboarding_status(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)],
):
    """
    Get current onboarding status and next step.

    Returns the user's current position in the onboarding flow
    and the next step they should complete.
    """
    logger.info(f"Getting onboarding status for user {auth0_id}")

    service = OnboardingProgressService(db)

    try:
        progress = await service.get_user_progress(auth0_id)
        next_step = await service.get_next_step(auth0_id)

        return OnboardingStatusResponse(
            success=True,
            message="Onboarding status retrieved",
            current_step=progress["current_step"],
            next_step=next_step,
            completed=progress["completed"],
            can_resume=not progress["completed"],
            progress_data=progress.get("data", {}),
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve onboarding status"
        )


@router.post("/track", response_model=OnboardingProgressResponse)
@limiter.limit(API_RATE_LIMIT)
async def track_onboarding_action(
    request: Request,
    action_request: OnboardingActionRequest,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)],
):
    """
    Track an onboarding action (internal use).

    This endpoint is used internally by other onboarding endpoints
    to track progress after successful operations.
    """
    logger.info(f"Tracking action {action_request.action} for user {auth0_id}")

    service = OnboardingProgressService(db)

    try:
        progress = await service.update_progress_on_action(
            auth0_id=auth0_id,
            action=action_request.action,
            action_data=action_request.data,
        )

        next_step = await service.get_next_step(auth0_id)

        return OnboardingProgressResponse(
            success=True,
            message=f"Progress updated: {progress['current_step']}",
            progress=progress,
            next_step=next_step,
        )

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to track action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track progress")


@router.post("/reset")
@limiter.limit(API_RATE_LIMIT)
async def reset_onboarding_progress(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)],
):
    """
    Reset user's onboarding progress (admin or testing).

    Clears all progress and returns user to the beginning of onboarding.
    """
    logger.warning(f"Resetting onboarding progress for user {auth0_id}")

    service = OnboardingProgressService(db)

    try:
        progress = await service.reset_progress(auth0_id)

        return {
            "success": True,
            "message": "Onboarding progress reset successfully",
            "current_step": progress["current_step"],
        }

    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reset progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset progress")
