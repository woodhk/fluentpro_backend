"""
Authentication Domain Service Interfaces

Defines contracts for authentication-related business services.
These interfaces abstract the business logic from implementation details.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IAuthService(ABC):
    """
    Authentication service interface for user authentication operations.
    
    Handles login, logout, token management, and user creation.
    """
    
    @abstractmethod
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing:
                - access_token: JWT access token
                - refresh_token: Refresh token for getting new access tokens
                - expires_in: Token expiration time in seconds
                - user_id: Authenticated user's ID
                
        Raises:
            AuthenticationError: If credentials are invalid
        """
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict containing:
                - access_token: New JWT access token
                - expires_in: Token expiration time in seconds
                
        Raises:
            TokenError: If refresh token is invalid or expired
        """
        pass
    
    @abstractmethod
    def logout(self, refresh_token: str) -> bool:
        """
        Logout user and revoke tokens.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if logout successful
            
        Raises:
            TokenError: If token revocation fails
        """
        pass
    
    @abstractmethod
    def create_user(self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user account.
        
        Args:
            email: User's email address
            password: User's password
            metadata: Optional user metadata
            
        Returns:
            Created user's ID
            
        Raises:
            UserCreationError: If user creation fails
            DuplicateUserError: If email already exists
        """
        pass
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from access token.
        
        Args:
            access_token: Valid JWT access token
            
        Returns:
            Dict containing user information
            
        Raises:
            TokenError: If token is invalid
        """
        pass
    
    @abstractmethod
    def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update user metadata.
        
        Args:
            user_id: User's ID
            metadata: Metadata to update
            
        Returns:
            True if update successful
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass
    
    @abstractmethod
    def verify_email(self, user_id: str) -> bool:
        """
        Send email verification.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if verification email sent
        """
        pass
    
    @abstractmethod
    def reset_password(self, email: str) -> bool:
        """
        Initiate password reset process.
        
        Args:
            email: User's email address
            
        Returns:
            True if reset email sent
        """
        pass


class ITokenService(ABC):
    """
    Token management service interface.
    
    Handles token generation, validation, and storage.
    """
    
    @abstractmethod
    def generate_access_token(self, user_id: str, claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a new access token.
        
        Args:
            user_id: User's ID
            claims: Optional additional claims to include
            
        Returns:
            JWT access token
        """
        pass
    
    @abstractmethod
    def generate_refresh_token(self, user_id: str) -> str:
        """
        Generate a new refresh token.
        
        Args:
            user_id: User's ID
            
        Returns:
            Refresh token
        """
        pass
    
    @abstractmethod
    def validate_access_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an access token and extract claims.
        
        Args:
            token: JWT access token
            
        Returns:
            Token claims
            
        Raises:
            TokenError: If token is invalid or expired
        """
        pass
    
    @abstractmethod
    def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a refresh token.
        
        Args:
            token: Refresh token
            
        Returns:
            Token metadata
            
        Raises:
            TokenError: If token is invalid or expired
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revocation successful
        """
        pass
    
    @abstractmethod
    def is_token_revoked(self, token: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token: Token to check
            
        Returns:
            True if token is revoked
        """
        pass
    
    @abstractmethod
    def get_token_expiry(self, token: str) -> datetime:
        """
        Get token expiration time.
        
        Args:
            token: Token to check
            
        Returns:
            Expiration datetime
        """
        pass


class IPasswordService(ABC):
    """
    Password management service interface.
    
    Handles password hashing, validation, and security policies.
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Hash a password using secure algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        pass
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Dict containing:
                - is_valid: Whether password meets requirements
                - errors: List of validation errors
                - score: Password strength score (0-100)
        """
        pass
    
    @abstractmethod
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        pass
    
    @abstractmethod
    def check_password_history(self, user_id: str, password: str) -> bool:
        """
        Check if password was previously used.
        
        Args:
            user_id: User's ID
            password: Password to check
            
        Returns:
            True if password was used before
        """
        pass


class ISessionService(ABC):
    """
    Session management service interface.
    
    Handles user session lifecycle and management.
    """
    
    @abstractmethod
    def create_session(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: User's ID
            device_info: Optional device/browser information
            
        Returns:
            Session ID
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data if found
        """
        pass
    
    @abstractmethod
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """
        End a user session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session ended
        """
        pass
    
    @abstractmethod
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            List of active sessions
        """
        pass
    
    @abstractmethod
    def end_all_sessions(self, user_id: str, except_current: Optional[str] = None) -> int:
        """
        End all sessions for a user.
        
        Args:
            user_id: User's ID
            except_current: Optional session ID to keep active
            
        Returns:
            Number of sessions ended
        """
        pass