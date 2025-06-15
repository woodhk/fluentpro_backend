from typing import Dict, Any, Optional
from datetime import date
from supabase import Client
from ...repositories.users.user_repository import UserRepository
from ...integrations.auth0 import auth0_client
from ...schemas.users.user import UserUpdate
from ...core.exceptions import UserNotFoundError, DatabaseError


class UserService:
    def __init__(self, db: Client):
        self.user_repo = UserRepository(db)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Auth0 ID"""
        return await self.user_repo.get_by_auth0_id(auth0_id)

    async def create_user_from_auth0(
        self, auth0_data: Dict[str, Any], date_of_birth: Optional[date] = None
    ) -> Dict[str, Any]:
        """Create user from Auth0 profile data"""
        from datetime import date

        user_data = {
            "auth0_id": auth0_data.get("sub"),
            "email": auth0_data.get("email"),
            "full_name": auth0_data.get("name"),
            "date_of_birth": date_of_birth if date_of_birth else date(
                1990, 1, 1
            ),  # Use provided DOB or default
            "is_active": True,
        }

        try:
            return await self.user_repo.create_user(user_data)
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {str(e)}")

    async def update_user_profile(
        self, user_id: str, update_data: UserUpdate
    ) -> Dict[str, Any]:
        """Update user profile"""
        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

        try:
            updated_user = await self.user_repo.update_user(user_id, update_dict)
            if not updated_user:
                raise UserNotFoundError(user_id)
            return updated_user
        except Exception as e:
            raise DatabaseError(f"Failed to update user: {str(e)}")

    async def sync_auth0_profile(self, auth0_id: str) -> Dict[str, Any]:
        """Sync user profile with Auth0 data"""
        # Get latest data from Auth0
        auth0_data = await auth0_client.get_user_profile(auth0_id)
        if not auth0_data:
            raise ValueError("Could not fetch Auth0 profile")

        # Get existing user from database
        user = await self.user_repo.get_by_auth0_id(auth0_id)

        if not user:
            # Create new user if doesn't exist
            return await self.create_user_from_auth0(auth0_data)
        else:
            # Update existing user with latest Auth0 data
            update_data = {
                "email": auth0_data.get("email"),
                "full_name": auth0_data.get("name"),
            }
            return await self.user_repo.update_user(user["id"], update_data)
