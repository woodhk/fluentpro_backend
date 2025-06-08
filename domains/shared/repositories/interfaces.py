"""
Shared repository interfaces that can be used across domains.
These interfaces define contracts for data access that are needed by multiple domains.
"""

from abc import abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.patterns.repository import IRepository


class IUserRepository(IRepository):
    """
    Shared user repository interface.
    This interface can be used by any domain that needs user operations.
    """
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Any]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def find_by_auth0_id(self, auth0_id: str) -> Optional[Any]:
        """Find user by Auth0 ID"""
        pass
    
    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        pass
    
    @abstractmethod
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        pass
    
    @abstractmethod
    async def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data"""
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: int = 20) -> List[Any]:
        """Search users by name or email"""
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        pass


class IRoleRepository(IRepository):
    """
    Shared role repository interface.
    This interface can be used by any domain that needs role operations.
    """
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Any]:
        """Find role by name"""
        pass
    
    @abstractmethod
    async def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[Any]:
        """Search roles by embedding similarity"""
        pass
    
    @abstractmethod
    async def get_by_industry(self, industry_id: str) -> List[Any]:
        """Get roles by industry"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics"""
        pass
    
    @abstractmethod
    async def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Any]:
        """Search roles by text query"""
        pass
    
    @abstractmethod
    async def get_roles_needing_embedding(self, limit: int = 100) -> List[Any]:
        """Get roles that don't have embeddings yet"""
        pass
    
    @abstractmethod
    async def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        """Update role embedding"""
        pass