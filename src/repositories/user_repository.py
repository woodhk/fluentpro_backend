from typing import Dict, Any, Optional, List
from datetime import date
from supabase import Client
from .base import SupabaseRepository
from ..core.exceptions import DatabaseError

class UserRepository(SupabaseRepository):
    """Repository for user data operations."""
    
    def __init__(self, db: Client):
        super().__init__(db, "users")
    
    async def get_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Auth0 ID."""
        try:
            return await self.get_by_field("auth0_id", auth0_id)
        except Exception as e:
            raise DatabaseError(f"Failed to get user by Auth0 ID: {str(e)}")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            return await self.get_by_field("email", email.lower())
        except Exception as e:
            raise DatabaseError(f"Failed to get user by email: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with proper data formatting."""
        try:
            # Format date of birth if present
            if 'date_of_birth' in user_data and user_data['date_of_birth']:
                if isinstance(user_data['date_of_birth'], date):
                    user_data['date_of_birth'] = user_data['date_of_birth'].isoformat()
            
            # Ensure email is lowercase
            if 'email' in user_data:
                user_data['email'] = user_data['email'].lower()
            
            return await self.create(user_data)
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user with proper data formatting."""
        try:
            # Format date of birth if present
            if 'date_of_birth' in update_data and update_data['date_of_birth']:
                if isinstance(update_data['date_of_birth'], date):
                    update_data['date_of_birth'] = update_data['date_of_birth'].isoformat()
            
            # Ensure email is lowercase if being updated
            if 'email' in update_data:
                update_data['email'] = update_data['email'].lower()
            
            return await self.update(user_id, update_data)
        except Exception as e:
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    async def get_active_users(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get all active users with pagination."""
        try:
            page = (offset // limit) + 1
            return await self.paginate(
                page=page,
                page_size=limit,
                filters={"is_active": True},
                order_by="created_at",
                order_desc=True
            )
        except Exception as e:
            raise DatabaseError(f"Failed to get active users: {str(e)}")
    
    async def search_by_name(self, name_pattern: str) -> List[Dict[str, Any]]:
        """Search users by name pattern."""
        try:
            return await self.search("full_name", name_pattern)
        except Exception as e:
            raise DatabaseError(f"Failed to search users by name: {str(e)}")
    
    async def deactivate_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Deactivate a user account."""
        try:
            return await self.update(user_id, {"is_active": False})
        except Exception as e:
            raise DatabaseError(f"Failed to deactivate user: {str(e)}")
    
    async def activate_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Activate a user account."""
        try:
            return await self.update(user_id, {"is_active": True})
        except Exception as e:
            raise DatabaseError(f"Failed to activate user: {str(e)}")
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user exists with the given email."""
        try:
            user = await self.get_by_email(email)
            return user is not None
        except Exception:
            return False
    
    async def exists_by_auth0_id(self, auth0_id: str) -> bool:
        """Check if a user exists with the given Auth0 ID."""
        try:
            user = await self.get_by_auth0_id(auth0_id)
            return user is not None
        except Exception:
            return False