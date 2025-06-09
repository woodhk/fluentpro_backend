from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ...core.dependencies import get_current_user, get_db
from ...core.exceptions import UserNotFoundError
from ...schemas.user import UserResponse, UserUpdate, UserProfile
from ...services.user_service import UserService
from typing import Dict, Any

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=current_user["id"],
        full_name=current_user.get("full_name"),
        email=current_user["email"],
        date_of_birth=current_user.get("date_of_birth"),
        is_active=current_user["is_active"]
    )

@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    profile_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Update current user profile"""
    user_service = UserService(db)
    
    try:
        updated_user = await user_service.update_user_profile(current_user["id"], profile_data)
        return UserProfile(
            id=updated_user["id"],
            full_name=updated_user.get("full_name"),
            email=updated_user["email"],
            date_of_birth=updated_user.get("date_of_birth"),
            is_active=updated_user["is_active"]
        )
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_by_id(
    user_id: str,
    db: Client = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)  # Ensure authenticated
):
    """Get user by ID (requires authentication)"""
    user_service = UserService(db)
    
    try:
        user = await user_service.get_user_by_id(user_id)
        return UserProfile(
            id=user["id"],
            full_name=user.get("full_name"),
            email=user["email"],
            date_of_birth=user.get("date_of_birth"),
            is_active=user["is_active"]
        )
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")