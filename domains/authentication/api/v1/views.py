"""
Authentication-related API views for FluentPro v1.
Handles user signup, login, logout, and token management.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

from core.view_base import CSRFExemptView, PublicView, VersionedView
from core.responses import APIResponse
from core.exceptions import ValidationError, AuthenticationError, ConflictError
from domains.authentication.dto.requests import LoginRequest, SignupRequest, RefreshTokenRequest, LogoutRequest
from domains.authentication.dto.responses import UserResponse, TokenResponse, AuthResponse
from domains.authentication.use_cases.authenticate_user import AuthenticateUser
from domains.authentication.use_cases.register_user import RegisterUser

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(PublicView, VersionedView):
    """
    User registration endpoint.
    Creates user in both Auth0 and internal database.
    """
    
    def post(self, request):
        """Handle user registration."""
        try:
            signup_request = SignupRequest(**request.data)
        except Exception as e:
            return APIResponse.error(
                message="Validation failed",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use RegisterUser use case
            register_use_case = RegisterUser(
                auth_service=self.services.auth,
                user_repository=self.services.user_repository
            )
            
            result = register_use_case.execute(
                email=signup_request.email,
                password=signup_request.password,
                full_name=signup_request.full_name
            )
            
            return APIResponse.success(
                data=result,
                status_code=status.HTTP_201_CREATED
            )
            
        except (ValidationError, ConflictError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Sign up error: {str(e)}")
            return APIResponse.error(
                message="Sign up failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(PublicView, VersionedView):
    """
    User authentication endpoint.
    Validates credentials and returns JWT tokens.
    """
    
    def post(self, request):
        """Handle user login."""
        try:
            login_request = LoginRequest(**request.data)
        except Exception as e:
            return APIResponse.error(
                message="Validation failed",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use AuthenticateUser use case
            auth_use_case = AuthenticateUser(
                auth_service=self.services.auth,
                user_repository=self.services.user_repository
            )
            
            result = auth_use_case.execute(
                email=login_request.email,
                password=login_request.password
            )
            
            return APIResponse.success(data=result)
            
        except AuthenticationError as e:
            if 'invalid_grant' in str(e).lower() or 'invalid credentials' in str(e).lower():
                return APIResponse.error(
                    message="Invalid credentials",
                    details="Email or password is incorrect",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return APIResponse.error(
                message="Login failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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