"""
User profile management views for FluentPro v1.
Handles user profile operations and data management.
"""

from rest_framework import status
from datetime import timedelta
import logging

from api.common.responses import APIResponse
from api.common.documentation import document_endpoint
from authentication.backends import Auth0JWTAuthentication
from core.view_base import AuthenticatedView, VersionedView, CachedView
from domains.authentication.dto.mappers import user_mapper
from authentication.business.user_manager import UserManager
from application.decorators import cache, audit_log

logger = logging.getLogger(__name__)


class UserProfileView(CachedView, VersionedView):
    """
    User profile endpoint with caching support.
    Returns current user's profile information.
    """
    authentication_classes = [Auth0JWTAuthentication]
    cache_timeout = 600  # 10 minutes cache
    
    @document_endpoint(
        summary="Get User Profile",
        description="Retrieve detailed user profile information"
    )
    @cache(key_prefix="user_profile", ttl=timedelta(minutes=15))
    def get(self, request):
        """Get current user profile."""
        try:
            auth0_id = self.get_auth0_user_id()
            
            # Get from database using business manager
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(auth0_id)
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    code="USER_NOT_FOUND",
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
            
            return APIResponse.success(data=profile_data)
            
        except Exception as e:
            logger.error(f"User profile error: {str(e)}")
            return APIResponse.error(
                message="Failed to get user profile",
                code="PROFILE_FETCH_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @document_endpoint(
        summary="Update User Profile",
        description="Update user profile information (partial update)"
    )
    @audit_log(action="profile_update", resource_type="user")
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
            
            return APIResponse.success(
                data=response_data,
                message="Profile updated successfully"
            )
            
        except Exception as e:
            logger.error(f"User profile update error: {str(e)}")
            return APIResponse.error(
                message="Failed to update user profile",
                code="PROFILE_UPDATE_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class UserSettingsView(AuthenticatedView, VersionedView):
    """
    User settings management endpoint.
    Handles user preferences and configuration.
    """
    authentication_classes = [Auth0JWTAuthentication]
    
    @document_endpoint(
        summary="Get User Settings",
        description="Retrieve user preferences and configuration"
    )
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
                code="SETTINGS_FETCH_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @document_endpoint(
        summary="Update User Settings",
        description="Update user preferences and configuration"
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
                code="SETTINGS_UPDATE_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class UserDeactivateView(AuthenticatedView, VersionedView):
    """
    User account deactivation endpoint.
    Handles account deletion/deactivation.
    """
    authentication_classes = [Auth0JWTAuthentication]
    
    @document_endpoint(
        summary="Deactivate User Account",
        description="Deactivate the current user account"
    )
    @audit_log(action="account_deactivation", resource_type="user")
    def post(self, request):
        """Deactivate user account."""
        try:
            auth0_id = self.get_auth0_user_id()
            user_manager = UserManager()
            
            # Deactivate user account
            user_manager.deactivate_user(auth0_id)
            
            return APIResponse.success(
                data={'message': 'Account deactivated successfully'}
            )
            
        except Exception as e:
            logger.error(f"User deactivation error: {str(e)}")
            return APIResponse.error(
                message="Failed to deactivate account",
                code="DEACTIVATION_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )