"""
Repository interfaces for the onboarding domain.
These interfaces define the contracts for data access in the onboarding context.
"""

from abc import abstractmethod
from typing import Optional, List, Dict, Any

from core.patterns.repository import IRepository


class IPartnerRepository(IRepository[Dict[str, Any], str]):
    """Interface for communication partner repository operations"""
    
    @abstractmethod
    async def get_partners(self) -> List[Dict[str, Any]]:
        """Get all active communication partners"""
        pass
    
    @abstractmethod
    async def get_units(self) -> List[Dict[str, Any]]:
        """Get all active communication units"""
        pass
    
    @abstractmethod
    async def get_user_partners(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's selected partners"""
        pass
    
    @abstractmethod
    async def get_user_units(self, user_id: str, partner_id: str) -> List[Dict[str, Any]]:
        """Get user's selected units for a partner"""
        pass
    
    @abstractmethod
    async def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Save user's partner selections"""
        pass
    
    @abstractmethod
    async def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Save user's unit selections for a partner"""
        pass
    
    @abstractmethod
    async def get_user_communication_needs(self, user_id: str) -> Dict[str, Any]:
        """Get complete communication needs for a user"""
        pass
    
    @abstractmethod
    async def get_partner_statistics(self) -> Dict[str, Any]:
        """Get communication partner usage statistics"""
        pass
    
    @abstractmethod
    async def get_unit_statistics(self) -> Dict[str, Any]:
        """Get communication unit usage statistics"""
        pass


class IIndustryRepository(IRepository[Dict[str, Any], str]):
    """Interface for industry repository operations"""
    
    @abstractmethod
    async def get_by_name(self, industry_name: str) -> Optional[Dict[str, Any]]:
        """Get industry by name"""
        pass
    
    @abstractmethod
    async def get_with_role_counts(self) -> List[Dict[str, Any]]:
        """Get industries with role counts"""
        pass
    
    @abstractmethod
    async def get_popular_industries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular industries based on user selections"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search industries by name or description"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get industry statistics"""
        pass