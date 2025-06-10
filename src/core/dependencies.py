from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import Client
from .auth import auth0_validator
from .database import get_db
from ..services.auth.auth_service import AuthService
from typing import Dict, Any

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user_auth0_id(token: str = Depends(security)) -> str:
    """Extract Auth0 user ID from JWT token"""
    try:
        payload = auth0_validator.verify_jwt_token(token.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user ID found"
            )
        return user_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

async def get_current_user(
    auth0_id: str = Depends(get_current_user_auth0_id),
    db: Client = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user from Supabase or create if doesn't exist"""
    auth_service = AuthService(db)
    return await auth_service.get_or_create_user(auth0_id)