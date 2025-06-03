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
from authentication.serializers import (
    SignUpSerializer, LoginSerializer, RefreshTokenSerializer, 
    LogoutSerializer, Auth0CallbackSerializer
)
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(PublicView, VersionedView):
    """
    User registration endpoint.
    Creates user in both Auth0 and internal database.
    """
    
    def post(self, request):
        """Handle user registration."""
        serializer = SignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extract validated data
            user_data = {
                'email': serializer.validated_data['email'],
                'password': serializer.validated_data['password'],
                'full_name': serializer.validated_data['full_name'],
                'date_of_birth': serializer.validated_data['date_of_birth'].isoformat()
            }
            
            # Use business manager for user creation
            user_manager = UserManager()
            
            # Check if user already exists
            existing_user = user_manager.get_user_by_email(user_data['email'])
            if existing_user:
                raise ConflictError(f"User with email '{user_data['email']}' already exists")
            
            # Create user through auth service and internal database
            auth_service = self.services.auth
            
            # Create user in Auth0
            auth0_user = auth_service.create_user(user_data)
            
            # Add Auth0 ID to user data for internal creation
            user_data['auth0_id'] = auth0_user['user_id']
            user_data['is_active'] = True
            
            # Create user in internal database
            internal_user = user_manager.create_user(user_data)
            
            # Authenticate the user to get tokens
            token_info = auth_service.authenticate(user_data['email'], user_data['password'])
            
            return APIResponse.success(
                data={
                    'access_token': token_info.access_token,
                    'refresh_token': token_info.refresh_token,
                    'token_type': token_info.token_type,
                    'expires_in': token_info.expires_in,
                    'user': {
                        'id': internal_user.id,
                        'full_name': internal_user.full_name,
                        'email': internal_user.email,
                        'date_of_birth': str(internal_user.date_of_birth)
                    }
                },
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
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate with Auth0
            auth_service = self.services.auth
            token_info = auth_service.authenticate(email, password)
            
            # Get user from internal database
            user_manager = UserManager()
            user = user_manager.get_user_by_email(email)
            
            if not user:
                return APIResponse.error(
                    message="User not found",
                    details="User does not exist in our system",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return APIResponse.success(
                data={
                    'access_token': token_info.access_token,
                    'refresh_token': token_info.refresh_token,
                    'token_type': token_info.token_type,
                    'expires_in': token_info.expires_in,
                    'user': {
                        'id': user.id,
                        'full_name': user.full_name,
                        'email': user.email,
                        'date_of_birth': str(user.date_of_birth)
                    }
                }
            )
            
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
        serializer = RefreshTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh_token = serializer.validated_data['refresh_token']
            
            # Refresh token with Auth0
            auth_service = self.services.auth
            token_info = auth_service.refresh_token(refresh_token)
            
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
        serializer = LogoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Validation failed",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh_token = serializer.validated_data['refresh_token']
            
            # Revoke refresh token
            auth_service = self.services.auth
            success = auth_service.logout_user(refresh_token)
            
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