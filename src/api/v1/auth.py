from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from ...core.dependencies import get_current_user_auth0_id, get_current_user, get_db
from ...core.rate_limiting import limiter, AUTH_RATE_LIMIT
from ...schemas.auth import AuthStatus, SignupRequest, SignupResponse
from ...services.auth_service import AuthService
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/status", response_model=AuthStatus)
@limiter.limit(AUTH_RATE_LIMIT)
async def get_auth_status(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authentication status"""
    return AuthStatus(
        authenticated=True,
        user_id=current_user.get("id"),
        message="User is authenticated"
    )

@router.get("/me")
@limiter.limit(AUTH_RATE_LIMIT)
async def get_current_user_info(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@router.get("/verify")
@limiter.limit(AUTH_RATE_LIMIT)
async def verify_token(request: Request, auth0_id: str = Depends(get_current_user_auth0_id)):
    """Verify JWT token and return Auth0 user ID"""
    return {
        "valid": True,
        "auth0_id": auth0_id,
        "message": "Token is valid"
    }

@router.post("/signup", response_model=SignupResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def signup_user(
    request: Request,
    signup_data: SignupRequest,
    db: Client = Depends(get_db)
):
    """Create a new user account"""
    try:
        auth_service = AuthService(db)
        
        result = await auth_service.signup_user(
            email=signup_data.email,
            password=signup_data.password,
            full_name=signup_data.full_name
        )
        
        return SignupResponse(
            success=result["success"],
            message=result["message"],
            user_id=result["user_id"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))