"""
Repository interfaces for the authentication domain.
These interfaces define the contracts for data access in the authentication context.
"""

from abc import abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.patterns.repository import IRepository
from domains.shared.repositories.interfaces import IUserRepository, IRoleRepository
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.authentication.models.role import Role, RoleMatch, HierarchyLevel


class IAuthUserRepository(IUserRepository):
    """Authentication-specific user repository interface extending shared interface"""
    
    @abstractmethod
    async def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        """Get users by onboarding status"""
        pass
    
    @abstractmethod
    async def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        """Bulk update onboarding status for multiple users"""
        pass


class IAuthRoleRepository(IRoleRepository):
    """Authentication-specific role repository interface extending shared interface"""
    
    # All methods are inherited from the shared interface
    # Add authentication-specific methods here if needed in the future
    pass