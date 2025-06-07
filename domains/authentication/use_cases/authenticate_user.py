"""
User authentication use case.

Handles user login and token generation.
"""

from typing import Optional, Dict, Any
import logging

from core.patterns.use_case import UseCase
from core.exceptions import (
    AuthenticationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.authentication.dto.requests import LoginRequest
from domains.authentication.dto.responses import AuthResponse, TokenResponse, UserResponse
from domains.authentication.services.interfaces import IAuthService
from domains.authentication.repositories.interfaces import IUserRepository

logger = logging.getLogger(__name__)


class AuthenticateUserUseCase(UseCase[LoginRequest, AuthResponse]):
    """
    Authenticates a user with email and password.
    
    Flow:
    1. Authenticate user via Auth0 service
    2. Verify user exists in Supabase database
    3. Check if user account is active
    4. Generate user and token response objects
    5. Return authentication response with tokens
    
    Errors:
    - AuthenticationError: Invalid email/password or deactivated account
    - SupabaseUserNotFoundError: User authenticated but not in database
    - BusinessLogicError: General authentication process failure
    
    Dependencies:
    - IAuthService: For Auth0 authentication
    - IUserRepository: To verify user existence and status
    """
    
    def __init__(
        self,
        auth_service: IAuthService,
        user_repository: IUserRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            auth_service: Authentication service for user authentication
            user_repository: Repository for user data operations
        """
        self.auth_service = auth_service
        self.user_repository = user_repository
    
    async def execute(self, request: LoginRequest) -> AuthResponse:
        """
        Execute user authentication.
        
        Args:
            request: LoginRequest containing email and password
            
        Returns:
            AuthResponse with user data and tokens
            
        Raises:
            AuthenticationError: If authentication fails
            SupabaseUserNotFoundError: If user not found in Supabase
            BusinessLogicError: If authentication process fails
        """
        try:
            # Authenticate via auth service
            try:
                auth_response = self.auth_service.authenticate(request.email, request.password)
            except Exception as e:
                logger.warning(f"Authentication failed for {request.email}: {str(e)}")
                raise AuthenticationError("Invalid email or password")
            
            # Verify user exists in our system
            user = await self.user_repository.find_by_email(request.email)
            if not user:
                logger.warning(f"User {request.email} authenticated but not found in our system")
                raise SupabaseUserNotFoundError(request.email)
            
            if not user.is_active:
                raise AuthenticationError("User account is deactivated")
            
            # Create response DTOs
            user_response = UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                created_at=user.created_at,
                updated_at=user.updated_at,
                is_active=user.is_active,
                onboarding_status=user.onboarding_status.value if user.onboarding_status else "pending",
                roles=["user"]
            )
            
            token_response = TokenResponse(
                access_token=auth_response.get("access_token", ""),
                refresh_token=auth_response.get("refresh_token", ""),
                expires_in=auth_response.get("expires_in", 3600)
            )
            
            return AuthResponse(user=user_response, tokens=token_response)
            
        except (AuthenticationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Authentication failed for {request.email}: {str(e)}")
            raise BusinessLogicError(f"Authentication failed: {str(e)}")