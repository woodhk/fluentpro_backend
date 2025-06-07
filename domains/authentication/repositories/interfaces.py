"""
Repository interfaces for the authentication domain.
These interfaces define the contracts for data access in the authentication context.
"""

from abc import abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.patterns.repository import IRepository
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.authentication.models.role import Role, RoleMatch, HierarchyLevel


class IUserRepository(IRepository[User, str]):
    """User repository interface extending base repository"""
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def find_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Find user by Auth0 ID"""
        pass
    
    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        pass
    
    @abstractmethod
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        pass
    
    @abstractmethod
    async def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data"""
        pass
    
    @abstractmethod
    async def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        """Get users by onboarding status"""
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by name or email"""
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        pass
    
    @abstractmethod
    async def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        """Bulk update onboarding status for multiple users"""
        pass


class IRoleRepository(IRepository[Role, str]):
    """Role repository interface"""
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Role]:
        """Find role by name"""
        pass
    
    @abstractmethod
    async def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        """Search roles by embedding similarity"""
        pass
    
    @abstractmethod
    async def get_by_industry(self, industry_id: str) -> List[Role]:
        """Get roles by industry"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics"""
        pass
    
    @abstractmethod
    async def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Role]:
        """Search roles by text query"""
        pass
    
    @abstractmethod
    async def get_roles_needing_embedding(self, limit: int = 100) -> List[Role]:
        """Get roles that don't have embeddings yet"""
        pass
    
    @abstractmethod
    async def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        """Update role embedding"""
        pass