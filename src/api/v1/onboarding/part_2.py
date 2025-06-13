from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from supabase import Client
from ....core.dependencies import get_current_user_auth0_id, get_db
from ....core.rate_limiting import limiter, API_RATE_LIMIT
from ....schemas.onboarding.part_2 import (
    GetCommunicationPartnersResponse,
    SelectCommunicationPartnersRequest, SelectCommunicationPartnersResponse,
    GetSituationsResponse, SelectSituationsRequest, SelectSituationsResponse,
    OnboardingPart2SummaryResponse
)
from ....services.onboarding.communication_service import CommunicationService
from ....services.onboarding.onboarding_progress_service import OnboardingProgressService
from ....core.logging import get_logger

router = APIRouter(prefix="/part-2", tags=["onboarding-part-2"])
logger = get_logger(__name__)


@router.get("/communication-partners", response_model=GetCommunicationPartnersResponse)
@limiter.limit(API_RATE_LIMIT)
async def get_communication_partners(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Get all available communication partners."""
    logger.info(f"Getting communication partners for user {auth0_id}")
    
    service = CommunicationService(db)
    
    try:
        result = await service.get_available_partners()
        
        return GetCommunicationPartnersResponse(
            success=True,
            message="Communication partners retrieved successfully",
            partners=result["partners"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get communication partners: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select-partners", response_model=SelectCommunicationPartnersResponse)
@limiter.limit(API_RATE_LIMIT)
async def select_communication_partners(
    request: Request,
    selection: SelectCommunicationPartnersRequest,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Select communication partners in priority order."""
    logger.info(f"User {auth0_id} selecting {len(selection.partner_ids)} partners")
    
    service = CommunicationService(db)
    progress_service = OnboardingProgressService(db)
    
    try:
        # Convert UUIDs to strings
        partner_ids = [str(pid) for pid in selection.partner_ids]
        
        result = await service.select_communication_partners(
            auth0_id=auth0_id,
            partner_ids=partner_ids
        )
        
        # Track progress after successful operation
        await progress_service.update_progress_on_action(
            auth0_id=auth0_id,
            action="select_communication_partners",
            action_data={"partner_ids": partner_ids, "count": len(partner_ids)}
        )
        
        return SelectCommunicationPartnersResponse(
            success=True,
            message=f"Selected {result['selected_count']} communication partners",
            selected_count=result["selected_count"],
            partner_selections=result["partner_selections"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save partner selections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/situations/{partner_id}", response_model=GetSituationsResponse)
@limiter.limit(API_RATE_LIMIT)
async def get_situations_for_partner(
    request: Request,
    partner_id: str,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Get available situations and user's selections for a specific partner."""
    logger.info(f"Getting situations for partner {partner_id}")
    
    service = CommunicationService(db)
    
    try:
        result = await service.get_situations_for_partner(
            auth0_id=auth0_id,
            partner_id=partner_id
        )
        
        return GetSituationsResponse(
            success=True,
            message="Situations retrieved successfully",
            partner_id=result["partner_id"],
            partner_name=result["partner_name"],
            available_situations=result["available_situations"],
            selected_situations=result["selected_situations"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get situations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select-situations", response_model=SelectSituationsResponse)
@limiter.limit(API_RATE_LIMIT)
async def select_situations_for_partner(
    request: Request,
    selection: SelectSituationsRequest,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Select situations for a specific communication partner."""
    logger.info(f"User {auth0_id} selecting situations for partner {selection.partner_id}")
    
    service = CommunicationService(db)
    progress_service = OnboardingProgressService(db)
    
    try:
        # Convert UUIDs to strings
        situation_ids = [str(sid) for sid in selection.situation_ids]
        
        result = await service.select_situations_for_partner(
            auth0_id=auth0_id,
            partner_id=str(selection.partner_id),
            situation_ids=situation_ids
        )
        
        # Track progress after successful operation
        await progress_service.update_progress_on_action(
            auth0_id=auth0_id,
            action="select_situations",
            action_data={
                "partner_id": str(selection.partner_id),
                "situation_ids": situation_ids,
                "count": len(situation_ids)
            }
        )
        
        return SelectSituationsResponse(
            success=True,
            message=f"Selected {result['selected_count']} situations",
            partner_id=result["partner_id"],
            selected_count=result["selected_count"],
            situation_selections=result["situation_selections"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save situation selections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=OnboardingPart2SummaryResponse)
@limiter.limit(API_RATE_LIMIT)
async def get_selections_summary(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Get summary of all user's selections."""
    logger.info(f"Getting selections summary for user {auth0_id}")
    
    service = CommunicationService(db)
    progress_service = OnboardingProgressService(db)
    
    try:
        result = await service.get_user_selections_summary(auth0_id)
        
        # Track that user viewed the summary
        await progress_service.update_progress_on_action(
            auth0_id=auth0_id,
            action="view_summary",
            action_data={"viewed_at": "now()"}
        )
        
        return OnboardingPart2SummaryResponse(
            success=True,
            message="Summary retrieved successfully",
            total_partners_selected=result["total_partners_selected"],
            total_situations_selected=result["total_situations_selected"],
            selections=result["selections"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
@limiter.limit(API_RATE_LIMIT)
async def complete_part_2(
    request: Request,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Complete Part 2 of onboarding and proceed to Part 3."""
    logger.info(f"Completing Part 2 for user {auth0_id}")
    
    service = CommunicationService(db)
    
    try:
        result = await service.complete_part_2(auth0_id)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "next_step": result["next_step"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete Part 2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))