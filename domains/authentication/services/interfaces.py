"""
Authentication Domain Service Interfaces

Defines contracts for authentication-related business services.
These interfaces abstract the business logic from implementation details.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IAuthenticationService(ABC):
    """External authentication service interface"""
    
    @abstractmethod
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        """Create user in external auth system, return auth_id"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return claims"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        pass


class ITokenService(ABC):
    """JWT token generation service"""
    
    @abstractmethod
    async def create_access_token(self, user_id: str, claims: Dict[str, Any]) -> str:
        """Create access token"""
        pass
    
    @abstractmethod
    async def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
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