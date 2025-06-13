from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from supabase import Client
from ....core.dependencies import get_current_user_auth0_id, get_db
from ....core.rate_limiting import limiter, API_RATE_LIMIT
from ....schemas.onboarding.part_1 import (
    NativeLanguageRequest, NativeLanguageResponse, 
    IndustryRequest, IndustryResponse,
    RoleSearchRequest, RoleSearchResponse, RoleMatch,
    RoleSelectionRequest, RoleSelectionResponse
)
from ....services.onboarding.profile_service import ProfileService
from ....services.onboarding.job_matching_service import JobMatchingService
from ....core.logging import get_logger

router = APIRouter(prefix="/part-1", tags=["onboarding-part-1"])
logger = get_logger(__name__)


@router.post("/native-language", response_model=NativeLanguageResponse)
@limiter.limit(API_RATE_LIMIT)
async def set_native_language(
    request: Request,
    language_request: NativeLanguageRequest,
    auth0_id: str = Depends(get_current_user_auth0_id),
    db: Client = Depends(get_db)
):
    """Set user's native language."""
    logger.info(f"Setting native language for user {auth0_id} to {language_request.native_language}")
    
    profile_service = ProfileService(db)
    
    try:
        result = await profile_service.update_native_language(
            auth0_id=auth0_id,
            native_language=language_request.native_language
        )
        
        return NativeLanguageResponse(
            success=True,
            message=f"Native language set to {language_request.native_language.value}",
            native_language=language_request.native_language
        )
        
    except Exception as e:
        logger.error(f"Failed to set native language: {str(e)}")
        raise


@router.post("/industry", response_model=IndustryResponse)
@limiter.limit(API_RATE_LIMIT)
async def set_industry(
    request: Request,
    industry_request: IndustryRequest,
    auth0_id: str = Depends(get_current_user_auth0_id),
    db: Client = Depends(get_db)
):
    """Set user's industry."""
    logger.info(f"Setting industry for user {auth0_id} to {industry_request.industry}")
    
    profile_service = ProfileService(db)
    
    try:
        result = await profile_service.update_industry(
            auth0_id=auth0_id,
            industry=industry_request.industry
        )
        
        return IndustryResponse(
            success=True,
            message=f"Industry set to {industry_request.industry.value}",
            industry=industry_request.industry
        )
        
    except Exception as e:
        logger.error(f"Failed to set industry: {str(e)}")
        raise


@router.post("/search-roles", response_model=RoleSearchResponse)
@limiter.limit(API_RATE_LIMIT)
async def search_roles(
    request: Request,
    search_request: RoleSearchRequest,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Search for matching roles based on job title and description."""
    logger.info(f"Searching roles for user {auth0_id}")
    
    job_matching_service = JobMatchingService(db)
    
    try:
        result = await job_matching_service.search_roles(
            auth0_id=auth0_id,
            job_title=search_request.job_title,
            job_description=search_request.job_description
        )
        
        # Convert to response format
        matches = [
            RoleMatch(
                id=match["id"],
                title=match["title"],
                description=match["description"],
                industry_name=match["industry_name"],
                confidence_score=match["confidence_score"]
            )
            for match in result["matches"]
        ]
        
        return RoleSearchResponse(
            success=True,
            message=f"Found {len(matches)} matching roles",
            matches=matches
        )
        
    except Exception as e:
        logger.error(f"Role search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.post("/select-role", response_model=RoleSelectionResponse)
@limiter.limit(API_RATE_LIMIT)
async def select_role(
    request: Request,
    selection_request: RoleSelectionRequest,
    auth0_id: Annotated[str, Depends(get_current_user_auth0_id)],
    db: Annotated[Client, Depends(get_db)]
):
    """Select a role or submit a custom role."""
    logger.info(f"Role selection for user {auth0_id}")
    
    job_matching_service = JobMatchingService(db)
    
    try:
        result = await job_matching_service.select_role(
            auth0_id=auth0_id,
            role_id=selection_request.role_id,
            custom_title=selection_request.custom_title,
            custom_description=selection_request.custom_description
        )
        
        return RoleSelectionResponse(
            success=result["success"],
            message=result["message"],
            role_id=result.get("role_id"),
            is_custom=result.get("is_custom", False)
        )
        
    except Exception as e:
        logger.error(f"Role selection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))