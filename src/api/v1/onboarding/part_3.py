"""API endpoints for Onboarding Part 3 - Summary and Completion."""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from supabase import Client
from ....core.dependencies import get_current_user_auth0_id, get_db
from ....core.rate_limiting import limiter, API_RATE_LIMIT
from ....schemas.onboarding.part_3 import (
    OnboardingSummaryResponse,
    OnboardingSummary,
    CompleteOnboardingResponse
)
from ....services.onboarding.summary_service import OnboardingSummaryService
from ....services.onboarding.onboarding_progress_service import OnboardingProgressService
from ....core.exceptions import UserNotFoundError
from ....core.logging import get_logger

router = APIRouter(prefix="/part-3", tags=["onboarding-part-3"])
logger = get_logger(__name__)


@router.get("/summary", response_model=OnboardingSummaryResponse)
@limiter.limit(API_RATE_LIMIT)
async def get_onboarding_summary(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """
    Get complete onboarding summary for the authenticated user.
    
    Returns a comprehensive summary including:
    - Native language selection
    - Industry selection
    - Role selection (predefined or custom)
    - Communication partners with their situations
    - Current onboarding status
    """
    logger.info(f"Getting onboarding summary for user {auth0_id}")
    
    service = OnboardingSummaryService(db)
    progress_service = OnboardingProgressService(db)
    
    try:
        # Get the summary
        summary = await service.get_onboarding_summary(auth0_id)
        
        # Track that user is viewing the final summary
        # This indicates they're ready to complete onboarding
        await progress_service.update_progress_on_action(
            auth0_id=auth0_id,
            action="view_summary",
            action_data={
                "viewed_final_summary": True,
                "is_complete": summary.get("is_complete", False),
                "timestamp": "now()"
            }
        )
        
        return OnboardingSummaryResponse(
            success=True,
            message="Onboarding summary retrieved successfully",
            summary=OnboardingSummary(**summary)
        )
        
    except UserNotFoundError as e:
        logger.warning(f"User not found: {auth0_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get onboarding summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve onboarding summary")


@router.post("/complete", response_model=CompleteOnboardingResponse)
@limiter.limit(API_RATE_LIMIT)
async def complete_onboarding(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """
    Complete the onboarding process.
    
    This endpoint validates that all required onboarding steps have been completed
    and updates the user's status to 'completed'.
    
    Returns:
    - Success confirmation
    - Updated onboarding status
    - Next steps for the user
    
    Raises:
    - 400 Bad Request if onboarding requirements are not met
    - 404 Not Found if user doesn't exist
    - 500 Internal Server Error for other failures
    """
    logger.info(f"Completing onboarding for user {auth0_id}")
    
    service = OnboardingSummaryService(db)
    progress_service = OnboardingProgressService(db)
    
    try:
        # Complete the onboarding
        result = await service.complete_onboarding(auth0_id)
        
        # Track final completion in progress tracking
        await progress_service.update_progress_on_action(
            auth0_id=auth0_id,
            action="complete_onboarding",
            action_data={
                "completed_at": "now()",
                "final_status": result["onboarding_status"]
            }
        )
        
        return CompleteOnboardingResponse(
            success=result["success"],
            message=result["message"],
            onboarding_status=result["onboarding_status"],
            next_steps=result.get("next_steps")
        )
        
    except ValueError as e:
        logger.warning(f"Onboarding incomplete for user {auth0_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFoundError as e:
        logger.warning(f"User not found: {auth0_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")