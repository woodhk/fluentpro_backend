"""
User authentication use case.

Handles user login and token generation.
"""

from typing import Optional, Dict, Any
import logging

from core.exceptions import (
    AuthenticationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.authentication.services.interfaces import IAuthService
from domains.authentication.repositories.interfaces import IUserRepository

logger = logging.getLogger(__name__)


class AuthenticateUser:
    """
    Use case for authenticating users.
    
    Handles user authentication with Auth0 and validates
    user existence in Supabase.
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
    
    async def execute(self, email: str, password: str) -> Dict[str, Any]:
        """
        Execute user authentication.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with authentication tokens
            
        Raises:
            AuthenticationError: If authentication fails
            SupabaseUserNotFoundError: If user not found in Supabase
            BusinessLogicError: If authentication process fails
        """
        try:
            # Authenticate via auth service
            try:
                auth_response = self.auth_service.authenticate(email, password)
            except Exception as e:
                logger.warning(f"Authentication failed for {email}: {str(e)}")
                raise AuthenticationError("Invalid email or password")
            
            # Verify user exists in our system
            user = await self.user_repository.find_by_email(email)
            if not user:
                logger.warning(f"User {email} authenticated but not found in our system")
                raise SupabaseUserNotFoundError(email)
            
            if not user.is_active:
                raise AuthenticationError("User account is deactivated")
            
            return auth_response
            
        except (AuthenticationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {str(e)}")
            raise BusinessLogicError(f"Authentication failed: {str(e)}")