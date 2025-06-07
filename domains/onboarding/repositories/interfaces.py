"""
Repository interfaces for the onboarding domain.
These interfaces define the contracts for data access in the onboarding context.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from onboarding.models.communication import (
    CommunicationPartner,
    Unit,
    UserCommunicationPartnerSelection,
    UserUnitSelection,
    UserCommunicationNeed
)


class IPartnerRepository(ABC):
    """Interface for communication partner repository operations."""
    
    @abstractmethod
    def get_partners(self) -> List[CommunicationPartner]:
        """Get all active communication partners."""
        pass
    
    @abstractmethod
    def get_units(self) -> List[Unit]:
        """Get all active communication units."""
        pass
    
    @abstractmethod
    def get_user_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """Get user's selected partners."""
        pass
    
    @abstractmethod
    def get_user_units(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """Get user's selected units for a partner."""
        pass
    
    @abstractmethod
    def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """Save user's partner selections."""
        pass
    
    @abstractmethod
    def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """Save user's unit selections for a partner."""
        pass
    
    @abstractmethod
    def get_user_communication_needs(self, user_id: str) -> UserCommunicationNeed:
        """Get complete communication needs for a user."""
        pass
    
    @abstractmethod
    def get_partner_statistics(self) -> Dict[str, Any]:
        """Get communication partner usage statistics."""
        pass
    
    @abstractmethod
    def get_unit_statistics(self) -> Dict[str, Any]:
        """Get communication unit usage statistics."""
        pass


class IIndustryRepository(ABC):
    """Interface for industry repository operations."""
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active industries."""
        pass
    
    @abstractmethod
    def get_by_id(self, industry_id: str) -> Optional[Dict[str, Any]]:
        """Get industry by ID."""
        pass
    
    @abstractmethod
    def get_by_name(self, industry_name: str) -> Optional[Dict[str, Any]]:
        """Get industry by name."""
        pass
    
    @abstractmethod
    def create(self, industry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new industry."""
        pass
    
    @abstractmethod
    def update(self, industry_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update industry data."""
        pass
    
    @abstractmethod
    def delete(self, industry_id: str) -> bool:
        """Soft delete industry by marking as inactive."""
        pass
    
    @abstractmethod
    def get_with_role_counts(self) -> List[Dict[str, Any]]:
        """Get industries with role counts."""
        pass
    
    @abstractmethod
    def get_popular_industries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular industries based on user selections."""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search industries by name or description."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get industry statistics."""
        pass