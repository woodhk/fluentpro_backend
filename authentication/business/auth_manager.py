"""
Business logic for authentication operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from core.exceptions import (
    AuthenticationError,
    Auth0Error,
    SupabaseUserNotFoundError,
    BusinessLogicError,
    ConflictError
)
from authentication.models.auth import TokenInfo, AuthSession, AuthProvider, UserRegistration
from authentication.models.user import User
from authentication.services.auth0_service import Auth0Service
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Business logic manager for authentication operations.
    Handles login, logout, registration, and token management.
    """
    
    def __init__(
        self, 
        auth0_service: Optional[Auth0Service] = None,
        user_manager: Optional[UserManager] = None
    ):
        self.auth0_service = auth0_service or Auth0Service()
        self.user_manager = user_manager or UserManager()
    
    def register_user(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user with Auth0 and Supabase.
        
        Args:
            registration_data: User registration information
            
        Returns:
            Dictionary with user data and tokens
            
        Raises:
            ValidationError: If registration data is invalid
            ConflictError: If user already exists
            Auth0Error: If Auth0 registration fails
        """
        try:
            # Validate registration data
            registration = UserRegistration(**registration_data)
            validation_errors = registration.validate()
            if validation_errors:
                from core.exceptions import ValidationError
                raise ValidationError("Registration validation failed", details=validation_errors)
            
            # Check if user already exists in our system
            existing_user = self.user_manager.get_user_by_email(registration.email)
            if existing_user:
                raise ConflictError(f"User with email '{registration.email}' already exists")
            
            # Create user in Auth0
            try:
                auth0_user = self.auth0_service.create_user(
                    registration.email,
                    registration.password,
                    registration.full_name
                )
            except Exception as e:
                logger.error(f"Auth0 user creation failed: {str(e)}")
                raise Auth0Error(f"Failed to create Auth0 user: {str(e)}")
            
            # Create user in Supabase
            user_data = {
                'full_name': registration.full_name,
                'email': registration.email,
                'date_of_birth': registration.date_of_birth,
                'auth0_id': auth0_user['user_id'],
                'is_active': True
            }
            
            supabase_user = self.user_manager.create_user(user_data)
            
            # Authenticate the user to get tokens
            token_info = self.authenticate_user(registration.email, registration.password)
            
            return {
                'user': supabase_user.to_dict(),
                'tokens': token_info.to_dict(),
                'onboarding_required': True
            }
            
        except (ConflictError, Auth0Error) as e:
            raise
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise BusinessLogicError(f"Registration failed: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> TokenInfo:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            TokenInfo with authentication tokens
            
        Raises:
            AuthenticationError: If authentication fails
            SupabaseUserNotFoundError: If user not found in Supabase
        """
        try:
            # Authenticate with Auth0
            try:
                auth_response = self.auth0_service.authenticate_user(email, password)
            except Exception as e:
                logger.warning(f"Auth0 authentication failed for {email}: {str(e)}")
                raise AuthenticationError("Invalid email or password")
            
            # Verify user exists in Supabase
            user = self.user_manager.get_user_by_email(email)
            if not user:
                logger.warning(f"User {email} authenticated with Auth0 but not found in Supabase")
                raise SupabaseUserNotFoundError(email)
            
            if not user.is_active:
                raise AuthenticationError("User account is deactivated")
            
            # Create token info
            token_info = TokenInfo(
                access_token=auth_response['access_token'],
                token_type=auth_response.get('token_type', 'Bearer'),
                expires_in=auth_response.get('expires_in', 3600),
                refresh_token=auth_response.get('refresh_token'),
                scope=auth_response.get('scope')
            )
            
            return token_info
            
        except (AuthenticationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            TokenInfo with new access token
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            auth_response = self.auth0_service.refresh_token(refresh_token)
            
            return TokenInfo(
                access_token=auth_response['access_token'],
                token_type=auth_response.get('token_type', 'Bearer'),
                expires_in=auth_response.get('expires_in', 3600),
                refresh_token=auth_response.get('refresh_token', refresh_token),
                scope=auth_response.get('scope')
            )
            
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    def logout_user(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Raises:
            AuthenticationError: If logout fails
        """
        try:
            success = self.auth0_service.revoke_refresh_token(refresh_token)
            if not success:
                raise AuthenticationError("Failed to revoke refresh token")
            
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            raise AuthenticationError(f"Logout failed: {str(e)}")
    
    def get_user_info_from_token(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from access token.
        
        Args:
            access_token: Access token
            
        Returns:
            User information from Auth0
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            return self.auth0_service.get_user_info(access_token)
            
        except Exception as e:
            logger.warning(f"Failed to get user info from token: {str(e)}")
            raise AuthenticationError("Invalid or expired access token")
    
    def create_auth_session(
        self, 
        user: User, 
        token_info: TokenInfo,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthSession:
        """
        Create an authentication session.
        
        Args:
            user: User instance
            token_info: Token information
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AuthSession instance
        """
        now = datetime.utcnow()
        
        return AuthSession(
            user_id=user.id,
            auth0_id=user.auth0_id,
            provider=AuthProvider.AUTH0,
            token_info=token_info,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
    
    def validate_user_credentials(self, email: str, password: str) -> Dict[str, Any]:
        """
        Validate user credentials without creating a session.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Try to authenticate with Auth0
            token_info = self.authenticate_user(email, password)
            user = self.user_manager.get_user_by_email(email)
            
            return {
                'valid': True,
                'user': user.to_dict() if user else None,
                'message': 'Credentials are valid'
            }
            
        except (AuthenticationError, SupabaseUserNotFoundError) as e:
            return {
                'valid': False,
                'user': None,
                'message': str(e)
            }
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return {
                'valid': False,
                'user': None,
                'message': 'Validation failed due to system error'
            }
    
    def update_user_metadata(self, auth0_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user metadata in Auth0.
        
        Args:
            auth0_id: Auth0 user ID
            metadata: Metadata to update
            
        Returns:
            Updated user data from Auth0
            
        Raises:
            Auth0Error: If metadata update fails
        """
        try:
            return self.auth0_service.update_user_metadata(auth0_id, metadata)
            
        except Exception as e:
            logger.error(f"Failed to update user metadata for {auth0_id}: {str(e)}")
            raise Auth0Error(f"Failed to update user metadata: {str(e)}")
    
    def send_email_verification(self, auth0_user_id: str) -> bool:
        """
        Send email verification to user.
        
        Args:
            auth0_user_id: Auth0 user ID
            
        Returns:
            True if verification email was sent successfully
        """
        try:
            return self.auth0_service.verify_email(auth0_user_id)
            
        except Exception as e:
            logger.error(f"Failed to send email verification for {auth0_user_id}: {str(e)}")
            return False