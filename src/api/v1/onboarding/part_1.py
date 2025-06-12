from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ....core.dependencies import get_current_user_auth0_id, get_db
from ....core.rate_limiting import limiter, API_RATE_LIMIT
from ....schemas.onboarding.part_1 import NativeLanguageRequest, NativeLanguageResponse
from ....services.onboarding.profile_service import ProfileService
from ....core.logging import get_logger
from fastapi import Request

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