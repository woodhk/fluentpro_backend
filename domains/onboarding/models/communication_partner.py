"""
Communication domain models for onboarding.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class CommunicationPartnerType(Enum):
    """Types of communication partners."""
    INTERNAL = "internal"  # Colleagues, supervisors, etc.
    EXTERNAL = "external"  # Clients, vendors, etc.
    CUSTOM = "custom"      # User-defined partners


class UnitType(Enum):
    """Types of communication units/situations."""
    MEETING = "meeting"
    PRESENTATION = "presentation"
    PHONE_CALL = "phone_call"
    NEGOTIATION = "negotiation"
    TRAINING = "training"
    CUSTOM = "custom"


@dataclass
class CommunicationPartner:
    """
    Represents a type of person/entity the user communicates with.
    """
    id: str
    name: str
    description: str
    partner_type: CommunicationPartnerType = CommunicationPartnerType.INTERNAL
    is_active: bool = True
    sort_order: int = 0
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert communication partner to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'partner_type': self.partner_type.value,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'CommunicationPartner':
        """Create CommunicationPartner from Supabase data."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        partner_type = CommunicationPartnerType.INTERNAL
        if data.get('partner_type'):
            try:
                partner_type = CommunicationPartnerType(data['partner_type'])
            except ValueError:
                pass
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            partner_type=partner_type,
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            created_at=created_at
        )


@dataclass
class Unit:
    """
    Represents a communication situation or context.
    """
    id: str
    name: str
    description: str
    unit_type: UnitType = UnitType.MEETING
    is_active: bool = True
    sort_order: int = 0
    skills_focus: List[str] = field(default_factory=list)
    difficulty_level: int = 1  # 1-5 scale
    created_at: Optional[datetime] = None
    
    @property
    def is_beginner_friendly(self) -> bool:
        """Check if unit is suitable for beginners."""
        return self.difficulty_level <= 2
    
    @property
    def is_advanced(self) -> bool:
        """Check if unit is advanced level."""
        return self.difficulty_level >= 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert unit to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'unit_type': self.unit_type.value,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'skills_focus': self.skills_focus,
            'difficulty_level': self.difficulty_level,
            'is_beginner_friendly': self.is_beginner_friendly,
            'is_advanced': self.is_advanced,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'Unit':
        """Create Unit from Supabase data."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        unit_type = UnitType.MEETING
        if data.get('unit_type'):
            try:
                unit_type = UnitType(data['unit_type'])
            except ValueError:
                pass
        
        skills_focus = data.get('skills_focus', [])
        if isinstance(skills_focus, str):
            # Handle case where skills are stored as comma-separated string
            skills_focus = [s.strip() for s in skills_focus.split(',') if s.strip()]
        elif not isinstance(skills_focus, list):
            skills_focus = []
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            unit_type=unit_type,
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            skills_focus=skills_focus,
            difficulty_level=data.get('difficulty_level', 1),
            created_at=created_at
        )


@dataclass
class UserCommunicationPartnerSelection:
    """
    Represents a user's selection of a communication partner.
    """
    user_id: str
    communication_partner_id: str
    partner_name: str
    priority: int
    is_custom: bool = False
    custom_partner_name: Optional[str] = None
    custom_partner_description: Optional[str] = None
    selected_at: Optional[datetime] = None
    
    @property
    def display_name(self) -> str:
        """Get the display name for this partner selection."""
        return self.custom_partner_name if self.is_custom else self.partner_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert partner selection to dictionary."""
        return {
            'user_id': self.user_id,
            'communication_partner_id': self.communication_partner_id,
            'partner_name': self.partner_name,
            'display_name': self.display_name,
            'priority': self.priority,
            'is_custom': self.is_custom,
            'custom_partner_name': self.custom_partner_name,
            'custom_partner_description': self.custom_partner_description,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None
        }


@dataclass
class UserUnitSelection:
    """
    Represents a user's selection of a communication unit for a specific partner.
    """
    user_id: str
    communication_partner_id: str
    unit_id: Optional[str]
    unit_name: str
    priority: int
    is_custom: bool = False
    custom_unit_name: Optional[str] = None
    custom_unit_description: Optional[str] = None
    selected_at: Optional[datetime] = None
    
    @property
    def display_name(self) -> str:
        """Get the display name for this unit selection."""
        return self.custom_unit_name if self.is_custom else self.unit_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert unit selection to dictionary."""
        return {
            'user_id': self.user_id,
            'communication_partner_id': self.communication_partner_id,
            'unit_id': self.unit_id,
            'unit_name': self.unit_name,
            'display_name': self.display_name,
            'priority': self.priority,
            'is_custom': self.is_custom,
            'custom_unit_name': self.custom_unit_name,
            'custom_unit_description': self.custom_unit_description,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None
        }


@dataclass
class UserCommunicationNeed:
    """
    Aggregated view of a user's communication needs.
    Combines partner and unit selections for a complete picture.
    """
    user_id: str
    partner_selections: List[UserCommunicationPartnerSelection] = field(default_factory=list)
    unit_selections: List[UserUnitSelection] = field(default_factory=list)
    
    @property
    def total_partners(self) -> int:
        """Get total number of selected partners."""
        return len(self.partner_selections)
    
    @property
    def total_units(self) -> int:
        """Get total number of selected units."""
        return len(self.unit_selections)
    
    @property
    def custom_partners_count(self) -> int:
        """Get number of custom partners."""
        return len([p for p in self.partner_selections if p.is_custom])
    
    @property
    def custom_units_count(self) -> int:
        """Get number of custom units."""
        return len([u for u in self.unit_selections if u.is_custom])
    
    def get_units_for_partner(self, partner_id: str) -> List[UserUnitSelection]:
        """Get all units selected for a specific partner."""
        return [
            unit for unit in self.unit_selections 
            if unit.communication_partner_id == partner_id
        ]
    
    def get_partners_by_priority(self) -> List[UserCommunicationPartnerSelection]:
        """Get partners sorted by priority."""
        return sorted(self.partner_selections, key=lambda x: x.priority)
    
    def get_units_by_priority(self, partner_id: Optional[str] = None) -> List[UserUnitSelection]:
        """Get units sorted by priority, optionally filtered by partner."""
        units = self.unit_selections
        if partner_id:
            units = self.get_units_for_partner(partner_id)
        return sorted(units, key=lambda x: x.priority)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert communication needs to dictionary."""
        partners_with_units = []
        
        for partner in self.get_partners_by_priority():
            partner_units = self.get_units_for_partner(partner.communication_partner_id)
            partners_with_units.append({
                'partner': partner.to_dict(),
                'units': [unit.to_dict() for unit in partner_units],
                'unit_count': len(partner_units)
            })
        
        return {
            'user_id': self.user_id,
            'summary': {
                'total_partners': self.total_partners,
                'total_units': self.total_units,
                'custom_partners_count': self.custom_partners_count,
                'custom_units_count': self.custom_units_count
            },
            'partners': [p.to_dict() for p in self.get_partners_by_priority()],
            'units': [u.to_dict() for u in self.get_units_by_priority()],
            'partners_with_units': partners_with_units
        }