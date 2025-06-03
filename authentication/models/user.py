"""
User domain models for authentication.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

from core.utils import calculate_age, validate_email

logger = logging.getLogger(__name__)


class OnboardingStatus(Enum):
    """Enumeration of possible onboarding statuses."""
    PENDING = "pending"
    WELCOME = "welcome"
    BASIC_INFO = "basic_info"
    AI_CONVERSATION = "ai_conversation"
    COURSE_ASSIGNMENT = "course_assignment"
    COMPLETED = "completed"


class NativeLanguage(Enum):
    """Enumeration of supported native languages."""
    ENGLISH = "english"
    CHINESE_TRADITIONAL = "chinese_traditional"
    CHINESE_SIMPLIFIED = "chinese_simplified"


@dataclass
class User:
    """
    Core user domain model representing a FluentPro user.
    """
    id: str
    full_name: str
    email: str
    date_of_birth: date
    auth0_id: str
    is_active: bool = True
    native_language: Optional[NativeLanguage] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not validate_email(self.email):
            raise ValueError(f"Invalid email address: {self.email}")
        
        if self.age < 13:
            raise ValueError("User must be at least 13 years old")
    
    @property
    def age(self) -> int:
        """Calculate user's current age."""
        return calculate_age(self.date_of_birth)
    
    @property
    def is_adult(self) -> bool:
        """Check if user is 18 or older."""
        return self.age >= 18
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'date_of_birth': self.date_of_birth.isoformat(),
            'age': self.age,
            'is_active': self.is_active,
            'native_language': self.native_language.value if self.native_language else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from Supabase data."""
        date_of_birth = data['date_of_birth']
        if isinstance(date_of_birth, str):
            date_of_birth = datetime.fromisoformat(date_of_birth).date()
        
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        # Handle native_language
        native_language = None
        if data.get('native_language'):
            try:
                native_language = NativeLanguage(data['native_language'])
            except ValueError:
                # If the database has an invalid value, log it but don't crash
                logger.warning(f"Invalid native_language value in database: {data.get('native_language')}")
        
        return cls(
            id=data['id'],
            full_name=data['full_name'],
            email=data['email'],
            date_of_birth=date_of_birth,
            auth0_id=data['auth0_id'],
            is_active=data.get('is_active', True),
            native_language=native_language,
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class UserProfile:
    """
    Extended user profile with onboarding and preference information.
    """
    user: User
    native_language: Optional[NativeLanguage] = None
    industry_id: Optional[str] = None
    industry_name: Optional[str] = None
    selected_role_id: Optional[str] = None
    role_title: Optional[str] = None
    role_description: Optional[str] = None
    onboarding_status: OnboardingStatus = OnboardingStatus.PENDING
    hierarchy_level: Optional[str] = None
    
    @property
    def has_completed_basic_info(self) -> bool:
        """Check if user has completed basic information."""
        return self.native_language is not None
    
    @property
    def has_selected_industry(self) -> bool:
        """Check if user has selected an industry."""
        return self.industry_id is not None
    
    @property
    def has_selected_role(self) -> bool:
        """Check if user has selected a role."""
        return self.selected_role_id is not None
    
    @property
    def onboarding_progress_percentage(self) -> int:
        """Calculate onboarding completion percentage."""
        total_steps = len(OnboardingStatus)
        current_step = list(OnboardingStatus).index(self.onboarding_status) + 1
        return int((current_step / total_steps) * 100)
    
    def can_access_phase(self, required_phase: OnboardingStatus) -> bool:
        """Check if user can access a specific onboarding phase."""
        phase_order = list(OnboardingStatus)
        required_index = phase_order.index(required_phase)
        current_index = phase_order.index(self.onboarding_status)
        return current_index >= required_index
    
    def advance_onboarding_status(self, new_status: OnboardingStatus) -> None:
        """Advance onboarding status if valid progression."""
        phase_order = list(OnboardingStatus)
        current_index = phase_order.index(self.onboarding_status)
        new_index = phase_order.index(new_status)
        
        if new_index > current_index:
            self.onboarding_status = new_status
        elif new_index < current_index:
            raise ValueError(f"Cannot move backwards from {self.onboarding_status.value} to {new_status.value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user profile to dictionary for API responses."""
        result = self.user.to_dict()
        result.update({
            'native_language': self.native_language.value if self.native_language else None,
            'industry_id': self.industry_id,
            'industry_name': self.industry_name,
            'selected_role_id': self.selected_role_id,
            'role_title': self.role_title,
            'role_description': self.role_description,
            'onboarding_status': self.onboarding_status.value,
            'onboarding_progress': self.onboarding_progress_percentage,
            'hierarchy_level': self.hierarchy_level,
            'has_completed_basic_info': self.has_completed_basic_info,
            'has_selected_industry': self.has_selected_industry,
            'has_selected_role': self.has_selected_role
        })
        return result
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile instance from Supabase data."""
        user = User.from_supabase_data(data)
        
        native_language = None
        if data.get('native_language'):
            try:
                native_language = NativeLanguage(data['native_language'])
            except ValueError:
                pass  # Invalid language value, keep as None
        
        onboarding_status = OnboardingStatus.PENDING
        if data.get('onboarding_status'):
            try:
                onboarding_status = OnboardingStatus(data['onboarding_status'])
            except ValueError:
                pass  # Invalid status value, keep as default
        
        return cls(
            user=user,
            native_language=native_language,
            industry_id=data.get('industry_id'),
            industry_name=data.get('industry_name'),
            selected_role_id=data.get('selected_role_id'),
            role_title=data.get('role_title'),
            role_description=data.get('role_description'),
            onboarding_status=onboarding_status,
            hierarchy_level=data.get('hierarchy_level')
        )


@dataclass
class UserPreferences:
    """
    User preferences and settings.
    """
    user_id: str
    email_notifications: bool = True
    push_notifications: bool = True
    language_preference: Optional[NativeLanguage] = None
    timezone: Optional[str] = None
    privacy_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary."""
        return {
            'user_id': self.user_id,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'language_preference': self.language_preference.value if self.language_preference else None,
            'timezone': self.timezone,
            'privacy_settings': self.privacy_settings
        }