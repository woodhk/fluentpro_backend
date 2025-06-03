"""
User repository implementation using Supabase.
Handles all user-related data access operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from core.interfaces import UserRepositoryInterface
from core.exceptions import (
    SupabaseUserNotFoundError,
    ValidationError,
    DatabaseError
)
from authentication.models.user import User, UserProfile, OnboardingStatus
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class UserRepository(UserRepositoryInterface):
    """
    Concrete implementation of UserRepositoryInterface using Supabase.
    Provides CRUD operations for users and user profiles.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase = supabase_service or SupabaseService()
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            response = self.supabase.client.table('users')\
                .select('*')\
                .eq('id', user_id)\
                .execute()
            
            if not response.data:
                return None
            
            return User.from_supabase_data(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    def get_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Get user by Auth0 ID."""
        try:
            response = self.supabase.client.table('users')\
                .select('*')\
                .eq('auth0_id', auth0_id)\
                .execute()
            
            if not response.data:
                return None
            
            return User.from_supabase_data(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by Auth0 ID {auth0_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            response = self.supabase.client.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if not response.data:
                return None
            
            return User.from_supabase_data(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user: {str(e)}")
    
    def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        try:
            # Validate required fields
            required_fields = ['auth0_id', 'email', 'full_name']
            for field in required_fields:
                if field not in user_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Set default values
            user_data.setdefault('onboarding_status', OnboardingStatus.PENDING.value)
            user_data.setdefault('created_at', datetime.utcnow().isoformat())
            user_data.setdefault('updated_at', datetime.utcnow().isoformat())
            
            response = self.supabase.client.table('users')\
                .insert(user_data)\
                .execute()
            
            if not response.data:
                raise DatabaseError("User creation failed - no data returned")
            
            return User.from_supabase_data(response.data[0])
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise DatabaseError(f"User creation failed: {str(e)}")
    
    def update(self, user_id: str, data: Dict[str, Any]) -> User:
        """Update user data."""
        try:
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.supabase.client.table('users')\
                .update(data)\
                .eq('id', user_id)\
                .execute()
            
            if not response.data:
                raise SupabaseUserNotFoundError(user_id)
            
            return User.from_supabase_data(response.data[0])
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise DatabaseError(f"User update failed: {str(e)}")
    
    def delete(self, user_id: str) -> bool:
        """Delete user."""
        try:
            response = self.supabase.client.table('users')\
                .delete()\
                .eq('id', user_id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise DatabaseError(f"User deletion failed: {str(e)}")
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        try:
            # First get the auth0_id for this user
            user = self.get_by_id(user_id)
            if not user:
                return None
            
            # Use the existing get_user_full_profile method which properly handles nested data
            profile_data = self.supabase.get_user_full_profile(user.auth0_id)
            if not profile_data:
                return None
            
            return UserProfile.from_supabase_data(profile_data)
            
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user profile: {str(e)}")
    
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile."""
        try:
            # Add updated timestamp
            profile_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.supabase.client.table('users')\
                .update(profile_data)\
                .eq('id', user_id)\
                .execute()
            
            if not response.data:
                raise SupabaseUserNotFoundError(user_id)
            
            # Get updated profile with joined data
            return self.get_profile(user_id)
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {str(e)}")
            raise DatabaseError(f"Profile update failed: {str(e)}")
    
    def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data."""
        try:
            return self.supabase.get_user_full_profile_by_auth0_id(auth0_id)
            
        except Exception as e:
            logger.error(f"Failed to get full profile for Auth0 ID {auth0_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve full profile: {str(e)}")
    
    def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        """Get users by onboarding status."""
        try:
            response = self.supabase.client.table('users')\
                .select('*')\
                .eq('onboarding_status', status.value)\
                .execute()
            
            return [User.from_supabase_data(user_data) for user_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get users by status {status}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve users by status: {str(e)}")
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name or email."""
        try:
            # Use ilike for case-insensitive search
            response = self.supabase.client.table('users')\
                .select('*')\
                .or_(f'full_name.ilike.%{query}%,email.ilike.%{query}%')\
                .limit(limit)\
                .execute()
            
            return [User.from_supabase_data(user_data) for user_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to search users with query '{query}': {str(e)}")
            raise DatabaseError(f"User search failed: {str(e)}")
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            # Get total users
            total_response = self.supabase.client.table('users')\
                .select('id', count='exact')\
                .execute()
            
            # Get users by status
            status_counts = {}
            for status in OnboardingStatus:
                status_response = self.supabase.client.table('users')\
                    .select('id', count='exact')\
                    .eq('onboarding_status', status.value)\
                    .execute()
                status_counts[status.value] = status_response.count
            
            # Get recent registrations (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            recent_response = self.supabase.client.table('users')\
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
    
    def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        """Bulk update onboarding status for multiple users."""
        try:
            update_data = {
                'onboarding_status': status.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.client.table('users')\
                .update(update_data)\
                .in_('id', user_ids)\
                .execute()
            
            return len(response.data)
            
        except Exception as e:
            logger.error(f"Failed to bulk update user status: {str(e)}")
            raise DatabaseError(f"Bulk status update failed: {str(e)}")