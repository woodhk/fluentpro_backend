"""
User registration use case.

Handles new user registration with Auth0 and Supabase.
"""

from typing import Dict, Any
import logging

from core.exceptions import (
    ValidationError,
    ConflictError,
    Auth0Error,
    BusinessLogicError
)
from authentication.models.auth import UserRegistration
from authentication.models.user import User
from domains.authentication.services.interfaces import IAuthService
from domains.authentication.repositories.interfaces import IUserRepository

logger = logging.getLogger(__name__)


class RegisterUser:
    """
    Use case for registering new users.
    
    Handles user registration with Auth0 and Supabase,
    including validation and initial authentication.
    """
    
    def __init__(
        self,
        auth_service: IAuthService,
        user_repository: IUserRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            auth_service: Authentication service for user creation
            user_repository: Repository for user data operations
        """
        self.auth_service = auth_service
        self.user_repository = user_repository
    
    async def execute(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute user registration.
        
        Args:
            registration_data: User registration information
                - email: User's email address
                - password: User's password
                - full_name: User's full name
                - date_of_birth: User's date of birth (optional)
                
        Returns:
            Dictionary with user data and tokens
            
        Raises:
            ValidationError: If registration data is invalid
            ConflictError: If user already exists
            Auth0Error: If Auth0 registration fails
            BusinessLogicError: If registration process fails
        """
        try:
            # Validate registration data
            registration = UserRegistration(**registration_data)
            validation_errors = registration.validate()
            if validation_errors:
                raise ValidationError("Registration validation failed", details=validation_errors)
            
            # Check if user already exists in our system
            existing_user = await self.user_repository.find_by_email(registration.email)
            if existing_user:
                raise ConflictError(f"User with email '{registration.email}' already exists")
            
            # Create user via auth service
            try:
                auth_user_id = self.auth_service.create_user(
                    registration.email,
                    registration.password,
                    metadata={
                        'full_name': registration.full_name,
                        'date_of_birth': registration.date_of_birth.isoformat() if registration.date_of_birth else None
                    }
                )
            except Exception as e:
                logger.error(f"Auth service user creation failed: {str(e)}")
                raise Auth0Error(f"Failed to create user: {str(e)}")
            
            # Create user in our database
            user = User(
                full_name=registration.full_name,
                email=registration.email,
                date_of_birth=registration.date_of_birth,
                auth0_id=auth_user_id,
                is_active=True
            )
            
            supabase_user = await self.user_repository.save(user)
            
            # Authenticate the user to get tokens
            auth_response = self.auth_service.authenticate(registration.email, registration.password)
            
            return {
                'user': supabase_user.to_dict(),
                'tokens': auth_response,
                'onboarding_required': True
            }
            
        except (ConflictError, Auth0Error, ValidationError):
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise BusinessLogicError(f"Registration failed: {str(e)}")