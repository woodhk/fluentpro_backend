"""
Onboarding response DTOs.
These DTOs define the structure of responses from onboarding operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class OnboardingStep(str, Enum):
    LANGUAGE_SELECTION = "language_selection"
    INDUSTRY_SELECTION = "industry_selection"
    ROLE_SELECTION = "role_selection"
    PARTNER_SELECTION = "partner_selection"
    SITUATION_CONFIGURATION = "situation_configuration"


class OnboardingStepResponse(BaseModel):
    """Individual onboarding step"""
    step_id: str
    name: str
    status: str
    completed_at: Optional[datetime] = None
    data: Dict[str, Any] = {}


class OnboardingSessionResponse(BaseModel):
    """Complete onboarding session response"""
    session_id: str
    user_id: str
    status: OnboardingStatus
    current_step: Optional[str] = None
    progress_percentage: int = Field(ge=0, le=100)
    steps: List[OnboardingStepResponse] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate session duration"""
        if self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    class Config:
        use_enum_values = True


class LanguageOption(BaseModel):
    """DTO for language option."""
    code: str = Field(..., description="Language code (e.g., 'en', 'es')")
    name: str = Field(..., description="Language name")
    native_name: str = Field(..., description="Language name in its native form")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "es",
                "name": "Spanish",
                "native_name": "Español"
            }
        }


class IndustryOption(BaseModel):
    """DTO for industry option."""
    id: str = Field(..., description="Industry unique identifier")
    name: str = Field(..., description="Industry name")
    description: Optional[str] = Field(None, description="Industry description")
    role_count: int = Field(0, description="Number of available roles in this industry")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174000",
                "name": "Technology",
                "description": "Software, hardware, and IT services",
                "role_count": 150
            }
        }


class RoleOption(BaseModel):
    """DTO for role option."""
    id: str = Field(..., description="Role unique identifier")
    title: str = Field(..., description="Role title")
    description: str = Field(..., description="Role description")
    hierarchy_level: str = Field(..., description="Role hierarchy level")
    relevance_score: Optional[float] = Field(None, description="Relevance score (for search results)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "title": "Software Engineer",
                "description": "Develops and maintains software applications",
                "hierarchy_level": "mid-level",
                "relevance_score": 0.95
            }
        }


class RoleMatchResponse(BaseModel):
    """DTO for role matching results."""
    matches: List[RoleOption] = Field(..., description="Matched roles sorted by relevance")
    suggested_role: Optional[RoleOption] = Field(None, description="Top suggested role")
    confidence_score: float = Field(..., description="Confidence score of the match")
    
    class Config:
        schema_extra = {
            "example": {
                "matches": [
                    {
                        "id": "456e7890-e89b-12d3-a456-426614174000",
                        "title": "Software Engineer",
                        "description": "Develops and maintains software applications",
                        "hierarchy_level": "mid-level",
                        "relevance_score": 0.95
                    }
                ],
                "suggested_role": {
                    "id": "456e7890-e89b-12d3-a456-426614174000",
                    "title": "Software Engineer",
                    "description": "Develops and maintains software applications",
                    "hierarchy_level": "mid-level",
                    "relevance_score": 0.95
                },
                "confidence_score": 0.95
            }
        }


class CommunicationPartnerOption(BaseModel):
    """DTO for communication partner option."""
    id: str = Field(..., description="Partner unique identifier")
    name: str = Field(..., description="Partner name")
    description: Optional[str] = Field(None, description="Partner description")
    icon: Optional[str] = Field(None, description="Icon identifier or URL")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "partner-1",
                "name": "Colleagues",
                "description": "Team members and coworkers",
                "icon": "users"
            }
        }


class CommunicationUnitOption(BaseModel):
    """DTO for communication unit/situation option."""
    id: str = Field(..., description="Unit unique identifier")
    name: str = Field(..., description="Unit/situation name")
    description: Optional[str] = Field(None, description="Unit description")
    example_phrases: Optional[List[str]] = Field(None, description="Example phrases for this situation")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "unit-1",
                "name": "Daily Standup",
                "description": "Brief daily team sync meeting",
                "example_phrases": [
                    "What did you work on yesterday?",
                    "What are you planning to do today?",
                    "Are there any blockers?"
                ]
            }
        }


class OnboardingStepResponse(BaseModel):
    """DTO for onboarding step completion response."""
    session_id: str = Field(..., description="Session ID")
    completed_step: OnboardingStep = Field(..., description="Step that was completed")
    next_step: Optional[OnboardingStep] = Field(None, description="Next step in the process")
    progress: Dict[str, bool] = Field(..., description="Updated progress")
    message: str = Field(..., description="Success message")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "completed_step": "language_selection",
                "next_step": "industry_selection",
                "progress": {
                    "language_selection": True,
                    "industry_selection": False,
                    "role_selection": False,
                    "partner_selection": False,
                    "situation_configuration": False
                },
                "message": "Language preferences saved successfully"
            }
        }


class OnboardingSummaryResponse(BaseModel):
    """DTO for onboarding completion summary."""
    user_id: str = Field(..., description="User ID")
    completed_at: datetime = Field(..., description="Completion timestamp")
    profile_summary: Dict[str, Any] = Field(..., description="Summary of user's profile")
    recommendations: List[str] = Field(default_factory=list, description="Personalized recommendations")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "completed_at": "2024-01-15T11:00:00Z",
                "profile_summary": {
                    "native_language": "Spanish",
                    "proficiency_level": "intermediate",
                    "industry": "Technology",
                    "role": "Software Engineer",
                    "communication_partners": ["Colleagues", "Clients"],
                    "total_situations": 15
                },
                "recommendations": [
                    "Start with basic technical vocabulary",
                    "Practice client presentation scenarios"
                ],
                "next_steps": [
                    "Complete your first lesson",
                    "Set up daily practice reminders"
                ]
            }
        }