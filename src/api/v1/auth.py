from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from ...core.dependencies import get_current_user_auth0_id, get_current_user, get_db
from ...core.rate_limiting import limiter, AUTH_RATE_LIMIT
from ...schemas.auth import AuthStatus, SignupRequest, SignupResponse
from ...services.user_service import UserService
from ...integrations.auth0 import Auth0Client
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
        # Initialize services
        auth0_client = Auth0Client()
        user_service = UserService(db)
        
        # Create user in Auth0
        auth0_user = await auth0_client.create_user(
            email=signup_data.email,
            password=signup_data.password,
            name=signup_data.full_name
        )
        
        # Create user in Supabase
        user_data = {
            "sub": auth0_user["user_id"],
            "email": auth0_user["email"],
            "name": auth0_user.get("name", signup_data.full_name)
        }
        
        supabase_user = await user_service.create_user_from_auth0(user_data)
        
        return SignupResponse(
            success=True,
            message="User created successfully",
            user_id=supabase_user["id"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")