from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import Client
from .auth import auth0_validator
from .database import get_db
from ..integrations.supabase import SupabaseUserRepository
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
    user_repo = SupabaseUserRepository(db)
    user = await user_repo.get_user_by_auth0_id(auth0_id)
    
    if not user:
        # Create user on first login with minimal data
        user_data = {
            "auth0_id": auth0_id,
            "is_active": True
        }
        user = await user_repo.create_user(user_data)
    
    return user