from fastapi import APIRouter, Depends, HTTPException
from ...core.dependencies import get_current_user_auth0_id, get_current_user
from ...schemas.auth import AuthStatus
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/status", response_model=AuthStatus)
async def get_auth_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authentication status"""
    return AuthStatus(
        authenticated=True,
        user_id=current_user.get("id"),
        message="User is authenticated"
    )

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@router.get("/verify")
async def verify_token(auth0_id: str = Depends(get_current_user_auth0_id)):
    """Verify JWT token and return Auth0 user ID"""
    return {
        "valid": True,
        "auth0_id": auth0_id,
        "message": "Token is valid"
    }