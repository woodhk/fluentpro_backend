from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from ..base import BaseResponse


class OnboardingStep(str):
    """Valid onboarding steps."""
    NOT_STARTED = "not_started"
    NATIVE_LANGUAGE = "native_language"
    INDUSTRY_SELECTION = "industry_selection"
    ROLE_INPUT = "role_input"
    ROLE_SELECTION = "role_selection"
    COMMUNICATION_PARTNERS = "communication_partners"
    SITUATION_SELECTION = "situation_selection"
    SUMMARY = "summary"
    COMPLETED = "completed"


class OnboardingProgress(BaseModel):
    """Onboarding progress model."""
    id: str
    user_id: str
    current_step: str
    data: Dict[str, Any] = Field(default_factory=dict)
    completed: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OnboardingProgressResponse(BaseResponse):
    """Response for onboarding progress."""
    progress: OnboardingProgress
    next_step: str


class OnboardingActionRequest(BaseModel):
    """Request to track an onboarding action."""
    action: str = Field(..., description="The action performed")
    data: Optional[Dict[str, Any]] = Field(None, description="Action-specific data to store")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = [
            "set_native_language", "set_industry", "search_roles",
            "select_role", "select_communication_partners",
            "select_situations", "view_summary", "complete_onboarding"
        ]
        if v not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {valid_actions}")
        return v


class OnboardingStatusResponse(BaseResponse):
    """Response for onboarding status check."""
    current_step: str
    next_step: str
    completed: bool
    can_resume: bool
    progress_data: Dict[str, Any]