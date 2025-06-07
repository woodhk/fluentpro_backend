"""
Authentication-related API views for FluentPro v1.
Handles user signup, login, logout, and token management.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

from api.common.base_views import BaseAPIView
from core.view_base import CSRFExemptView, PublicView, VersionedView
from core.responses import APIResponse
from core.exceptions import ValidationError, AuthenticationError, ConflictError
from domains.authentication.dto.requests import LoginRequest, SignupRequest, RefreshTokenRequest, LogoutRequest
from domains.authentication.dto.responses import UserResponse, TokenResponse, AuthResponse
from application.container import container

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(BaseAPIView, PublicView, VersionedView):
    """
    User registration endpoint.
    Creates user in both Auth0 and internal database.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_user = container.auth_use_cases.register_user()
    
    async def post(self, request):
        """Handle user registration."""
        # Parse request
        try:
            signup_request = SignupRequest(**request.data)
        except Exception as e:
            return Response(
                {"errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case
        return await self.handle_use_case(self.register_user, signup_request)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(BaseAPIView, PublicView, VersionedView):
    """
    User authentication endpoint.
    Validates credentials and returns JWT tokens.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.authenticate_user = container.auth_use_cases.authenticate_user()
    
    async def post(self, request):
        """Handle user login."""
        # Parse request
        try:
            login_request = LoginRequest(**request.data)
        except Exception as e:
            return Response(
                {"errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case
        return await self.handle_use_case(self.authenticate_user, login_request)


@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(PublicView, VersionedView):
    """
    Token refresh endpoint.
    Exchanges refresh token for new access token.
    """
    
    def post(self, request):
        """Handle token refresh."""
        try:
            refresh_request = RefreshTokenRequest(**request.data)
        except Exception as e:
            return APIResponse.error(
                message="Validation failed",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Refresh token with Auth0
            auth_service = self.services.auth
            token_info = auth_service.refresh_token(refresh_request.refresh_token)
            
            return APIResponse.success(
                data={
                    'access_token': token_info.access_token,
                    'refresh_token': token_info.refresh_token,
                    'token_type': token_info.token_type,
                    'expires_in': token_info.expires_in
                }
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return APIResponse.error(
                message="Token refresh failed",
                details=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED
            )


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(CSRFExemptView, VersionedView):
    """
    User logout endpoint.
    Revokes refresh token to invalidate session.
    """
    
    def post(self, request):
        """Handle user logout."""
        try:
            logout_request = LogoutRequest(**request.data)
        except Exception as e:
            return APIResponse.error(
                message="Validation failed",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Revoke refresh token
            auth_service = self.services.auth
            success = auth_service.logout_user(logout_request.refresh_token)
            
            if success:
                return APIResponse.success(
                    data={'message': 'Successfully logged out'}
                )
            else:
                return APIResponse.error(
                    message="Logout failed",
                    details="Failed to revoke token",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return APIResponse.error(
                message="Logout failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class Auth0CallbackView(PublicView, VersionedView):
    """
    Auth0 OAuth callback endpoint.
    Handles OAuth flow completion (placeholder for future implementation).
    """
    
    def post(self, request):
        """Handle Auth0 OAuth callback."""
        serializer = Auth0CallbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Placeholder for OAuth callback processing
            # This can be extended to handle OAuth flows in the future
            return APIResponse.success(
                data={'message': 'Auth0 callback received'}
            )
            
        except Exception as e:
            logger.error(f"Auth0 callback error: {str(e)}")
            return APIResponse.error(
                message="Callback processing failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )