"""
Repository interfaces for the authentication domain.
These interfaces define the contracts for data access in the authentication context.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from authentication.models.user import User, UserProfile, OnboardingStatus
from authentication.models.role import Role, RoleMatch, HierarchyLevel


class IUserRepository(ABC):
    """Interface for user repository operations."""
    
    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        pass
    
    @abstractmethod
    def find_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Find user by Auth0 ID."""
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Save (create or update) a user."""
        pass
    
    @abstractmethod
    def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    def update(self, user_id: str, data: Dict[str, Any]) -> User:
        """Update user data."""
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete user."""
        pass
    
    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        pass
    
    @abstractmethod
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile."""
        pass
    
    @abstractmethod
    def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data."""
        pass
    
    @abstractmethod
    def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        """Get users by onboarding status."""
        pass
    
    @abstractmethod
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name or email."""
        pass
    
    @abstractmethod
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics."""
        pass
    
    @abstractmethod
    def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        """Bulk update onboarding status for multiple users."""
        pass


class IRoleRepository(ABC):
    """Interface for role repository operations."""
    
    @abstractmethod
    def find_by_id(self, role_id: str) -> Optional[Role]:
        """Find role by ID."""
        pass
    
    @abstractmethod
    def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        """Search roles by embedding similarity."""
        pass
    
    @abstractmethod
    def create(self, role_data: Dict[str, Any]) -> Role:
        """Create a new role."""
        pass
    
    @abstractmethod
    def update(self, role_id: str, data: Dict[str, Any]) -> Role:
        """Update role data."""
        pass
    
    @abstractmethod
    def get_by_industry(self, industry_id: str) -> List[Role]:
        """Get roles by industry."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics."""
        pass
    
    @abstractmethod
    def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Role]:
        """Search roles by text query."""
        pass
    
    @abstractmethod
    def get_roles_needing_embedding(self, limit: int = 100) -> List[Role]:
        """Get roles that don't have embeddings yet."""
        pass
    
    @abstractmethod
    def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        """Update role embedding."""
        pass