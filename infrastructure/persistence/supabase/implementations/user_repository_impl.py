"""
User repository implementation using Supabase.
Concrete implementation of IUserRepository for data persistence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from domains.authentication.repositories.interfaces import IUserRepository
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.shared.repositories.base_repository import BaseRepository
from infrastructure.persistence.supabase.client import ISupabaseClient
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class UserRepositoryImpl(BaseRepository[User, str], IUserRepository):
    """
    Concrete implementation of IUserRepository using Supabase.
    Provides CRUD operations for users and user profiles.
    """
    
    def __init__(self, supabase_client: ISupabaseClient):
        super().__init__('users')
        self.client = supabase_client
    
    async def find_by_id(self, id: str) -> Optional[User]:
        """Find user by ID."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('id', id)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[User]:
        """Find all users matching filters."""
        try:
            query = self.client.table(self.table_name).select('*')
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = await query.execute()
            return [self._to_entity(user_data) for user_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get users with filters {filters}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve users: {str(e)}")
    
    async def save(self, entity: User) -> User:
        """Save entity (create or update)."""
        try:
            data = self._to_dict(entity)
            
            if entity.id:
                # Update existing user
                data['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .update(data)\
                    .eq('id', entity.id)\
                    .execute()
                
                if not response.data:
                    raise ResourceNotFoundError("User", entity.id)
                
                return self._to_entity(response.data[0])
            else:
                # Create new user
                data['created_at'] = datetime.utcnow().isoformat()
                data['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .insert(data)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("User creation failed - no data returned")
                
                created_user = self._to_entity(response.data[0])
                # Mark as registered to trigger domain events
                created_user.mark_as_registered(created_user.id)
                return created_user
                
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to save user: {str(e)}")
            raise DatabaseError(f"User save failed: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete user by ID."""
        try:
            response = await self.client.table(self.table_name)\
                .delete()\
                .eq('id', id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete user {id}: {str(e)}")
            raise DatabaseError(f"User deletion failed: {str(e)}")
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    async def find_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Find user by Auth0 ID."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('auth0_id', auth0_id)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by Auth0 ID {auth0_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        try:
            # Get user with joined profile data
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name), roles(id, title, description)')\
                .eq('id', user_id)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_profile(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user profile: {str(e)}")
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile."""
        try:
            # Add updated timestamp
            profile_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = await self.client.table(self.table_name)\
                .update(profile_data)\
                .eq('id', user_id)\
                .execute()
            
            if not response.data:
                raise ResourceNotFoundError("User", user_id)
            
            # Get updated profile with joined data
            profile = await self.get_profile(user_id)
            if not profile:
                raise ResourceNotFoundError("UserProfile", user_id)
            
            return profile
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {str(e)}")
            raise DatabaseError(f"Profile update failed: {str(e)}")
    
    async def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name), roles(id, title, description)')\
                .eq('auth0_id', auth0_id)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to get full profile for Auth0 ID {auth0_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve full profile: {str(e)}")
    
    async def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        """Get users by onboarding status."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('onboarding_status', status.value)\
                .execute()
            
            return [self._to_entity(user_data) for user_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get users by status {status}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve users by status: {str(e)}")
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name or email."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .or_(f'full_name.ilike.%{query}%,email.ilike.%{query}%')\
                .limit(limit)\
                .execute()
            
            return [self._to_entity(user_data) for user_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to search users with query '{query}': {str(e)}")
            raise DatabaseError(f"User search failed: {str(e)}")
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            # Get total users
            total_response = await self.client.table(self.table_name)\
                .select('id', count='exact')\
                .execute()
            
            # Get users by status
            status_counts = {}
            for status in OnboardingStatus:
                status_response = await self.client.table(self.table_name)\
                    .select('id', count='exact')\
                    .eq('onboarding_status', status.value)\
                    .execute()
                status_counts[status.value] = status_response.count
            
            # Get recent registrations (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            recent_response = await self.client.table(self.table_name)\
                .select('id', count='exact')\
                .gte('created_at', thirty_days_ago)\
                .execute()
            
            return {
                'total_users': total_response.count,
                'by_status': status_counts,
                'recent_registrations': recent_response.count,
                'completion_rate': (
                    status_counts.get('completed', 0) / max(total_response.count, 1) * 100
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user statistics: {str(e)}")
    
    async def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        """Bulk update onboarding status for multiple users."""
        try:
            update_data = {
                'onboarding_status': status.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = await self.client.table(self.table_name)\
                .update(update_data)\
                .in_('id', user_ids)\
                .execute()
            
            return len(response.data)
            
        except Exception as e:
            logger.error(f"Failed to bulk update user status: {str(e)}")
            raise DatabaseError(f"Bulk status update failed: {str(e)}")
    
    def _to_entity(self, data: Dict[str, Any]) -> User:
        """Convert database row to User entity."""
        return User.from_supabase_data(data)
    
    def _to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User entity to database row."""
        return {
            'email': entity.email,
            'full_name': entity.full_name,
            'date_of_birth': entity.date_of_birth.isoformat(),
            'auth0_id': entity.auth0_id,
            'is_active': entity.is_active,
            'native_language': entity.native_language.value if entity.native_language else None,
        }
    
    def _to_profile(self, data: Dict[str, Any]) -> UserProfile:
        """Convert database row to UserProfile entity."""
        return UserProfile.from_supabase_data(data)