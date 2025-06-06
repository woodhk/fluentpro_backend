"""
Auth0 Client Interface

Defines the contract for Auth0 API client implementation.
This interface abstracts Auth0-specific operations from the domain layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IAuth0Client(ABC):
    """
    Auth0 client interface for authentication provider operations.
    
    This interface provides low-level Auth0 API operations that are
    consumed by the domain authentication service.
    """
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str, 
                         connection: str = "Username-Password-Authentication") -> Dict[str, Any]:
        """
        Authenticate a user using Auth0's authentication API.
        
        Args:
            email: User's email address
            password: User's password
            connection: Auth0 connection name
            
        Returns:
            Dict containing:
                - access_token: JWT access token
                - refresh_token: Refresh token
                - id_token: ID token
                - expires_in: Token expiration in seconds
                - token_type: Token type (e.g., "Bearer")
                
        Raises:
            Auth0Error: If authentication fails
        """
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict containing:
                - access_token: New JWT access token
                - expires_in: Token expiration in seconds
                - token_type: Token type
                
        Raises:
            Auth0Error: If refresh fails
        """
        pass
    
    @abstractmethod
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if revocation successful
            
        Raises:
            Auth0Error: If revocation fails
        """
        pass
    
    @abstractmethod
    def create_user(self, email: str, password: str, 
                   connection: str = "Username-Password-Authentication",
                   user_metadata: Optional[Dict[str, Any]] = None,
                   app_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new user in Auth0.
        
        Args:
            email: User's email address
            password: User's password
            connection: Auth0 connection name
            user_metadata: Optional user metadata
            app_metadata: Optional app metadata
            
        Returns:
            Dict containing created user information
            
        Raises:
            Auth0Error: If user creation fails
        """
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Auth0.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            Dict containing user information
            
        Raises:
            Auth0Error: If user not found
        """
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by email.
        
        Args:
            email: User's email address
            
        Returns:
            User information if found, None otherwise
            
        Raises:
            Auth0Error: If search fails
        """
        pass
    
    @abstractmethod
    def update_user(self, user_id: str, 
                   user_metadata: Optional[Dict[str, Any]] = None,
                   app_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update user information in Auth0.
        
        Args:
            user_id: Auth0 user ID
            user_metadata: Optional user metadata updates
            app_metadata: Optional app metadata updates
            
        Returns:
            Updated user information
            
        Raises:
            Auth0Error: If update fails
        """
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from Auth0.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            True if deletion successful
            
        Raises:
            Auth0Error: If deletion fails
        """
        pass
    
    @abstractmethod
    def send_verification_email(self, user_id: str) -> bool:
        """
        Send email verification to user.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            True if email sent successfully
            
        Raises:
            Auth0Error: If sending fails
        """
        pass
    
    @abstractmethod
    def change_password(self, email: str, connection: str = "Username-Password-Authentication") -> bool:
        """
        Send password reset email.
        
        Args:
            email: User's email address
            connection: Auth0 connection name
            
        Returns:
            True if reset email sent
            
        Raises:
            Auth0Error: If sending fails
        """
        pass
    
    @abstractmethod
    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get user activity logs from Auth0.
        
        Args:
            user_id: Auth0 user ID
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log entries
            
        Raises:
            Auth0Error: If retrieval fails
        """
        pass
    
    @abstractmethod
    def block_user(self, user_id: str) -> bool:
        """
        Block a user account.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            True if user blocked successfully
            
        Raises:
            Auth0Error: If blocking fails
        """
        pass
    
    @abstractmethod
    def unblock_user(self, user_id: str) -> bool:
        """
        Unblock a user account.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            True if user unblocked successfully
            
        Raises:
            Auth0Error: If unblocking fails
        """
        pass
    
    @abstractmethod
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for a user.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            List of active sessions
            
        Raises:
            Auth0Error: If retrieval fails
        """
        pass
    
    @abstractmethod
    def invalidate_all_sessions(self, user_id: str) -> bool:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            True if sessions invalidated
            
        Raises:
            Auth0Error: If invalidation fails
        """
        pass


class IAuth0ManagementClient(ABC):
    """
    Auth0 Management API client interface.
    
    Provides administrative operations for Auth0 tenant management.
    """
    
    @abstractmethod
    def get_client_grant(self) -> str:
        """
        Get management API access token.
        
        Returns:
            Management API access token
            
        Raises:
            Auth0Error: If token retrieval fails
        """
        pass
    
    @abstractmethod
    def list_users(self, page: int = 0, per_page: int = 50, 
                  search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        List users with pagination.
        
        Args:
            page: Page number (0-based)
            per_page: Number of users per page
            search_query: Optional search query
            
        Returns:
            Dict containing users and pagination info
            
        Raises:
            Auth0Error: If listing fails
        """
        pass
    
    @abstractmethod
    def get_roles(self) -> List[Dict[str, Any]]:
        """
        Get all roles defined in Auth0.
        
        Returns:
            List of roles
            
        Raises:
            Auth0Error: If retrieval fails
        """
        pass
    
    @abstractmethod
    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: Auth0 user ID
            role_id: Auth0 role ID
            
        Returns:
            True if assignment successful
            
        Raises:
            Auth0Error: If assignment fails
        """
        pass
    
    @abstractmethod
    def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: Auth0 user ID
            role_id: Auth0 role ID
            
        Returns:
            True if removal successful
            
        Raises:
            Auth0Error: If removal fails
        """
        pass
    
    @abstractmethod
    def get_connections(self) -> List[Dict[str, Any]]:
        """
        Get all authentication connections.
        
        Returns:
            List of connections
            
        Raises:
            Auth0Error: If retrieval fails
        """
        pass