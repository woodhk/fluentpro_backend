"""
Authentication-related API views for FluentPro v1.
Handles user signup, login, logout, and token management.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from datetime import timedelta
import logging

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes

from api.common.base_views import BaseAPIView
from api.common.responses import APIResponse
from api.common.documentation import document_endpoint
from authentication.backends import Auth0JWTAuthentication
from core.view_base import CSRFExemptView, PublicView, VersionedView
from domains.authentication.dto.requests import LoginRequest, SignupRequest, RefreshTokenRequest, LogoutRequest
from domains.authentication.dto.responses import UserResponse, TokenResponse, AuthResponse
from domains.authentication.dto.mappers import user_mapper
from application.container import container
from application.decorators import validate_input, audit_log, cache

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(BaseAPIView, PublicView, VersionedView):
    """
    User registration endpoint.
    Creates user in both Auth0 and internal database.
    """
    
    @document_endpoint(
        summary="User Registration",
        description="Register a new user account",
        request_examples=[{
            "name": "Valid Registration",
            "value": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "full_name": "John Doe",
                "accept_terms": True
            }
        }]
    )
    async def post(self, request):
        """Handle user registration."""
        # Parse and validate request
        try:
            signup_dto = SignupRequest(**request.data)
        except ValidationError as e:
            return APIResponse.validation_error(e.errors())
        
        # Execute use case
        use_case = container.auth_use_cases.register_user()
        auth_response = await use_case.execute(signup_dto)
        
        # Return DTO response
        return APIResponse.success(
            auth_response.dict(),
            status_code=status.HTTP_201_CREATED
        )


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema_view(
    post=extend_schema(
        summary="User Login",
        description="Authenticate user with email and password. Returns JWT tokens for subsequent API calls.",
        tags=["Authentication"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string', 'minLength': 8},
                    'remember_me': {'type': 'boolean', 'default': False}
                },
                'required': ['email', 'password']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        name="Successful login",
                        value={
                            "data": {
                                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                "refresh_token": "def50200b5d3e2e8f6a8f7e9c4d3b2a1...",
                                "token_type": "Bearer",
                                "expires_in": 3600
                            },
                            "meta": {
                                "timestamp": "2024-01-15T10:30:00Z",
                                "version": "v1"
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Invalid credentials",
                        value={
                            "error": {
                                "code": "INVALID_CREDENTIALS",
                                "message": "Invalid email or password"
                            }
                        }
                    )
                ]
            ),
            422: OpenApiResponse(description="Validation errors")
        },
        examples=[
            OpenApiExample(
                name="Basic login",
                request_only=True,
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123!"
                }
            ),
            OpenApiExample(
                name="Login with remember me",
                request_only=True,
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123!",
                    "remember_me": True
                }
            )
        ]
    )
)
class LoginView(BaseAPIView, PublicView, VersionedView):
    """
    User authentication endpoint.
    Validates credentials and returns JWT tokens.
    """
    authentication_classes = []  # Public endpoint
    permission_classes = []
    
    async def post(self, request):
        """Handle user login."""
        # Parse and validate request
        try:
            login_dto = LoginRequest(**request.data)
        except ValidationError as e:
            return APIResponse.validation_error(e.errors())
        
        # Execute use case
        use_case = container.auth_use_cases.authenticate_user()
        auth_response = await use_case.execute(login_dto)
        
        # Return DTO response
        return APIResponse.success(
            auth_response.dict(),
            status_code=status.HTTP_200_OK
        )


@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(BaseAPIView, PublicView, VersionedView):
    """
    Token refresh endpoint.
    Exchanges refresh token for new access token.
    """
    
    @document_endpoint(
        summary="Refresh Token",
        description="Exchange refresh token for new access token",
        request_examples=[{
            "name": "Valid Refresh",
            "value": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }]
    )
    def post(self, request):
        """Handle token refresh."""
        # Parse and validate request
        try:
            refresh_dto = RefreshTokenRequest(**request.data)
        except ValidationError as e:
            return APIResponse.validation_error(e.errors())
        
        try:
            # Refresh token with Auth0
            auth_service = self.services.auth
            token_info = auth_service.refresh_token(refresh_dto.refresh_token)
            
            # Create token response DTO
            token_response = TokenResponse(
                access_token=token_info.access_token,
                refresh_token=token_info.refresh_token,
                token_type=token_info.token_type,
                expires_in=token_info.expires_in
            )
            
            return APIResponse.success(token_response.dict())
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return APIResponse.error(
                message="Token refresh failed",
                code="TOKEN_REFRESH_ERROR",
                status_code=status.HTTP_401_UNAUTHORIZED
            )


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(BaseAPIView, CSRFExemptView, VersionedView):
    """
    User logout endpoint.
    Revokes refresh token to invalidate session.
    """
    
    @document_endpoint(
        summary="User Logout",
        description="Revoke refresh token and end user session",
        request_examples=[{
            "name": "Valid Logout",
            "value": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }]
    )
    def post(self, request):
        """Handle user logout."""
        # Parse and validate request
        try:
            logout_dto = LogoutRequest(**request.data)
        except ValidationError as e:
            return APIResponse.validation_error(e.errors())
        
        try:
            # Revoke refresh token
            auth_service = self.services.auth
            success = auth_service.logout_user(logout_dto.refresh_token)
            
            if success:
                return APIResponse.success(
                    data={'message': 'Successfully logged out'}
                )
            else:
                return APIResponse.error(
                    message="Logout failed",
                    code="LOGOUT_ERROR",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return APIResponse.error(
                message="Logout failed",
                code="LOGOUT_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class Auth0CallbackView(BaseAPIView, PublicView, VersionedView):
    """
    Auth0 OAuth callback endpoint.
    Handles OAuth flow completion (placeholder for future implementation).
    """
    
    @document_endpoint(
        summary="Auth0 OAuth Callback",
        description="Handle OAuth flow completion from Auth0",
        request_examples=[{
            "name": "OAuth Callback",
            "value": {
                "code": "authorization_code",
                "state": "random_state_string"
            }
        }]
    )
    def post(self, request):
        """Handle Auth0 OAuth callback."""
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
                code="OAUTH_CALLBACK_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(BaseAPIView):
    """
    User profile endpoint.
    Retrieves current user profile information.
    """
    authentication_classes = [Auth0JWTAuthentication]
    
    @document_endpoint(
        summary="Get User Profile",
        description="Retrieve current user profile information",
        response_examples=[{
            "name": "User Profile Response",
            "value": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_verified": False,
                "profile_completion": 85,
                "roles": ["user"]
            }
        }]
    )
    async def get(self, request, user_id: str = None):
        """Get current user profile."""
        # Get current user if no ID provided
        if not user_id or user_id == 'me':
            user_id = request.user.auth0_id
        
        # Execute use case
        use_case = container.auth_use_cases.get_user_profile()
        user = await use_case.execute(user_id)
        
        # Map to DTO and return
        user_dto = user_mapper.to_dto(user)
        return APIResponse.success(
            user_dto.dict(),
            status_code=status.HTTP_200_OK
        )