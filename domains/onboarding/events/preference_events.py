"""
Onboarding preference and selection-related domain events.
These events track user preferences selected during onboarding.
"""

from typing import List, Optional, Dict, Any

from domains.shared.events.base_event import DomainEvent


class LanguageSelectedEvent(DomainEvent):
    """Event raised when a user selects their language preferences."""
    
    user_id: str
    session_id: str
    native_language: str
    target_language: str
    proficiency_level: str
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.language_selected",
            aggregate_id=data.get('user_id'),
            **data
        )


class IndustrySelectedEvent(DomainEvent):
    """Event raised when a user selects their industry."""
    
    user_id: str
    session_id: str
    industry_id: str
    industry_name: str
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.industry_selected",
            aggregate_id=data.get('user_id'),
            **data
        )


class RoleSelectedEvent(DomainEvent):
    """Event raised when a user selects or creates their professional role."""
    
    user_id: str
    session_id: str
    role_id: Optional[str] = None
    role_title: str
    role_description: str
    is_custom_role: bool = False
    hierarchy_level: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.role_selected",
            aggregate_id=data.get('user_id'),
            **data
        )


class CustomRoleCreatedEvent(DomainEvent):
    """Event raised when a user creates a custom role during onboarding."""
    
    user_id: str
    session_id: str
    role_id: str
    role_title: str
    role_description: str
    industry_id: str
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.custom_role_created",
            aggregate_id=data.get('role_id'),
            **data
        )


class RoleMatchPerformedEvent(DomainEvent):
    """Event raised when role matching is performed from job description."""
    
    user_id: str
    session_id: str
    job_description: str
    matched_roles: List[Dict[str, Any]]
    selected_role_id: Optional[str] = None
    confidence_score: float
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.role_match_performed",
            aggregate_id=data.get('user_id'),
            **data
        )


class CommunicationPartnersSelectedEvent(DomainEvent):
    """Event raised when a user selects their communication partners."""
    
    user_id: str
    session_id: str
    selected_partner_ids: List[str]
    custom_partners: List[str]
    total_partners: int
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.communication_partners_selected",
            aggregate_id=data.get('user_id'),
            **data
        )


class PartnerSituationsConfiguredEvent(DomainEvent):
    """Event raised when a user configures situations for a communication partner."""
    
    user_id: str
    session_id: str
    partner_id: str
    partner_name: str
    selected_unit_ids: List[str]
    custom_units: List[str]
    total_situations: int
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.partner_situations_configured",
            aggregate_id=data.get('user_id'),
            **data
        )


class LearningGoalsDefinedEvent(DomainEvent):
    """Event raised when a user defines their learning goals."""
    
    user_id: str
    session_id: str
    primary_goals: List[str]
    timeline: str  # "1_month", "3_months", "6_months", "1_year"
    daily_time_commitment: int  # minutes per day
    preferred_learning_style: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.learning_goals_defined",
            aggregate_id=data.get('user_id'),
            **data
        )


class PersonalizationCompleteEvent(DomainEvent):
    """Event raised when user personalization is complete."""
    
    user_id: str
    session_id: str
    profile_completion_score: float  # 0.0 to 1.0
    personalization_features: List[str]
    recommendations_generated: int
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.personalization_complete",
            aggregate_id=data.get('user_id'),
            **data
        )