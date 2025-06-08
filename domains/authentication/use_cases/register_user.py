"""
User registration use case.

Handles new user registration with Auth0 and Supabase.
"""

from typing import Dict, Any
import logging

from core.patterns.use_case import UseCase
from core.exceptions import (
    ValidationError,
    ConflictError,
    Auth0Error,
    BusinessLogicError
)
from domains.authentication.dto.requests import SignupRequest
from domains.authentication.dto.responses import AuthResponse, TokenResponse, UserResponse
from authentication.models.auth import UserRegistration
from authentication.models.user import User
from domains.authentication.services.interfaces import IAuthService
from domains.authentication.repositories.interfaces import IAuthUserRepository

logger = logging.getLogger(__name__)


class RegisterUserUseCase(UseCase[SignupRequest, AuthResponse]):
    """
    Registers a new user in the system.
    
    Flow:
    1. Check if user already exists in database
    2. Create user in Auth0 with email and password
    3. Save user record in Supabase database
    4. Authenticate user to get initial tokens
    5. Return authentication response with user data
    
    Errors:
    - ValidationError: Invalid registration data
    - ConflictError: User with email already exists
    - Auth0Error: Failed to create user in Auth0
    - BusinessLogicError: General registration process failure
    
    Dependencies:
    - IAuthService: For Auth0 user creation and authentication
    - IUserRepository: To check existence and save user data
    """
    
    def __init__(
        self,
        auth_service: IAuthService,
        user_repository: IAuthUserRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            auth_service: Authentication service for user creation
            user_repository: Repository for user data operations
        """
        self.auth_service = auth_service
        self.user_repository = user_repository
    
    async def execute(self, request: SignupRequest) -> AuthResponse:
        """
        Execute user registration.
        
        Args:
            request: SignupRequest containing registration information
                
        Returns:
            AuthResponse with user data and tokens
            
        Raises:
            ValidationError: If registration data is invalid
            ConflictError: If user already exists
            Auth0Error: If Auth0 registration fails
            BusinessLogicError: If registration process fails
        """
        try:
            # Check if user already exists in our system
            existing_user = await self.user_repository.find_by_email(request.email)
            if existing_user:
                raise ConflictError(f"User with email '{request.email}' already exists")
            
            # Create user via auth service
            try:
                auth_user_id = self.auth_service.create_user(
                    request.email,
                    request.password,
                    metadata={
                        'full_name': request.full_name
                    }
                )
            except Exception as e:
                logger.error(f"Auth service user creation failed: {str(e)}")
                raise Auth0Error(f"Failed to create user: {str(e)}")
            
            # Create user in our database
            user = User(
                full_name=request.full_name,
                email=request.email,
                auth0_id=auth_user_id,
                is_active=True
            )
            
            supabase_user = await self.user_repository.save(user)
            
            # Authenticate the user to get tokens
            auth_response = self.auth_service.authenticate(request.email, request.password)
            
            # Create response DTOs
            user_response = UserResponse(
                id=str(supabase_user.id),
                email=supabase_user.email,
                full_name=supabase_user.full_name,
                created_at=supabase_user.created_at,
                updated_at=supabase_user.updated_at,
                is_active=supabase_user.is_active,
                onboarding_status="pending",
                roles=["user"]
            )
            
            token_response = TokenResponse(
                access_token=auth_response.get("access_token", ""),
                refresh_token=auth_response.get("refresh_token", ""),
                expires_in=auth_response.get("expires_in", 3600)
            )
            
            return AuthResponse(user=user_response, tokens=token_response)
            
        except (ConflictError, Auth0Error, ValidationError):
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise BusinessLogicError(f"Registration failed: {str(e)}")