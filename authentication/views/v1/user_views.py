"""
User profile management views for FluentPro v1.
Handles user profile operations and data management.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class UserProfileView(CachedView, VersionedView):
    """
    User profile endpoint with caching support.
    Returns current user's profile information.
    """
    cache_timeout = 600  # 10 minutes cache
    
    def get(self, request):
        """Get current user profile."""
        try:
            auth0_id = self.get_auth0_user_id()
            
            # Check cache first
            cache_key = self.get_cache_key("profile", auth0_id)
            cached_profile = self.get_cached_response(cache_key)
            
            if cached_profile:
                return APIResponse.success(data=cached_profile)
            
            # Get from database using business manager
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(auth0_id)
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Format response data
            profile_data = {
                'id': user_profile.user.id,
                'full_name': user_profile.user.full_name,
                'email': user_profile.user.email,
                'date_of_birth': str(user_profile.user.date_of_birth),
                'native_language': user_profile.native_language.value if user_profile.native_language else None,
                'industry': {
                    'id': user_profile.industry_id,
                    'name': user_profile.industry_name
                } if user_profile.industry_id else None,
                'role': {
                    'id': user_profile.selected_role_id,
                    'title': user_profile.role_title
                } if user_profile.selected_role_id else None,
                'onboarding_status': user_profile.onboarding_status.value,
                'created_at': user_profile.user.created_at.isoformat() if user_profile.user.created_at else None,
                'updated_at': user_profile.user.updated_at.isoformat() if user_profile.user.updated_at else None
            }
            
            # Cache the response
            self.set_cached_response(cache_key, profile_data)
            
            return APIResponse.success(data=profile_data)
            
        except Exception as e:
            logger.error(f"User profile error: {str(e)}")
            return APIResponse.error(
                message="Failed to get user profile",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update user profile (partial update)."""
        try:
            auth0_id = self.get_auth0_user_id()
            user_manager = UserManager()
            
            # Handle specific profile updates
            response_data = {}
            
            # Update native language if provided
            if 'native_language' in request.data:
                result = user_manager.update_native_language(
                    auth0_id, 
                    request.data['native_language']
                )
                response_data['native_language'] = result
            
            # Update industry if provided
            if 'industry_id' in request.data:
                result = user_manager.update_industry(
                    auth0_id,
                    request.data['industry_id']
                )
                response_data['industry'] = result
            
            # Update selected role if provided
            if 'role_id' in request.data:
                result = user_manager.update_selected_role(
                    auth0_id,
                    request.data['role_id']
                )
                response_data['role'] = result
            
            # Clear user cache after updates
            cache_key = self.get_cache_key("profile", auth0_id)
            self.delete(cache_key)
            
            return APIResponse.success(
                data=response_data,
                message="Profile updated successfully"
            )
            
        except Exception as e:
            logger.error(f"User profile update error: {str(e)}")
            return APIResponse.error(
                message="Failed to update user profile",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


class UserSettingsView(AuthenticatedView, VersionedView):
    """
    User settings management endpoint.
    Handles user preferences and configuration.
    """
    
    def get(self, request):
        """Get user settings."""
        try:
            user = self.get_current_user()
            
            settings_data = {
                'notifications': {
                    'email_enabled': True,
                    'push_enabled': True
                },
                'privacy': {
                    'profile_visible': True,
                    'data_sharing': False
                },
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC'
                }
            }
            
            return APIResponse.success(data=settings_data)
            
        except Exception as e:
            logger.error(f"User settings error: {str(e)}")
            return APIResponse.error(
                message="Failed to get user settings",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update user settings."""
        try:
            # Settings update logic here
            # For now, just return success
            
            return APIResponse.success(
                data={'message': 'Settings updated successfully'}
            )
            
        except Exception as e:
            logger.error(f"User settings update error: {str(e)}")
            return APIResponse.error(
                message="Failed to update user settings",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


class UserDeactivateView(AuthenticatedView, VersionedView):
    """
    User account deactivation endpoint.
    Handles account deletion/deactivation.
    """
    
    def post(self, request):
        """Deactivate user account."""
        try:
            auth0_id = self.get_auth0_user_id()
            user_manager = UserManager()
            
            # Deactivate user account
            user_manager.deactivate_user(auth0_id)
            
            # Clear all user cache
            cache_key_prefix = f"user:{auth0_id}"
            # Implementation depends on cache backend
            
            return APIResponse.success(
                data={'message': 'Account deactivated successfully'}
            )
            
        except Exception as e:
            logger.error(f"User deactivation error: {str(e)}")
            return APIResponse.error(
                message="Failed to deactivate account",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )