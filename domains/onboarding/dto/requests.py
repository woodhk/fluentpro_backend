"""
Onboarding request DTOs.
These DTOs define the structure of incoming requests for onboarding operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class ProficiencyLevel(str, Enum):
    """Language proficiency levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"


class StartOnboardingRequest(BaseModel):
    """DTO for starting the onboarding process."""
    user_id: str = Field(..., description="User ID to start onboarding for")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class SelectLanguageRequest(BaseModel):
    """DTO for selecting native language and proficiency level."""
    session_id: str = Field(..., description="Onboarding session ID")
    native_language: str = Field(..., min_length=2, max_length=50, description="User's native language")
    proficiency_level: ProficiencyLevel = Field(..., description="User's proficiency level in target language")
    target_language: Optional[str] = Field("English", description="Language the user wants to learn")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "native_language": "Spanish",
                "proficiency_level": "intermediate",
                "target_language": "English"
            }
        }


class SelectIndustryRequest(BaseModel):
    """DTO for selecting user's industry."""
    session_id: str = Field(..., description="Onboarding session ID")
    industry_id: str = Field(..., description="Selected industry ID")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "industry_id": "789e0123-e89b-12d3-a456-426614174000"
            }
        }


class SelectRoleRequest(BaseModel):
    """DTO for selecting or creating user's professional role."""
    session_id: str = Field(..., description="Onboarding session ID")
    role_id: Optional[str] = Field(None, description="Selected existing role ID")
    custom_role_title: Optional[str] = Field(None, min_length=3, max_length=100, description="Custom role title")
    custom_role_description: Optional[str] = Field(None, min_length=10, max_length=500, description="Custom role description")
    
    @validator('role_id', 'custom_role_title')
    def validate_role_selection(cls, v, values):
        """Ensure either role_id or custom role data is provided."""
        if not v and not values.get('custom_role_title'):
            raise ValueError('Either role_id or custom_role_title must be provided')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "role_id": "456e7890-e89b-12d3-a456-426614174000"
            }
        }


class RoleDescriptionMatchRequest(BaseModel):
    """DTO for matching role from job description."""
    session_id: str = Field(..., description="Onboarding session ID")
    job_description: str = Field(..., min_length=50, max_length=2000, description="Job description text")
    industry_id: Optional[str] = Field(None, description="Industry ID to narrow down search")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "job_description": "We are looking for a Software Engineer to develop and maintain web applications...",
                "industry_id": "789e0123-e89b-12d3-a456-426614174000"
            }
        }


class SelectCommunicationPartnersRequest(BaseModel):
    """DTO for selecting communication partners."""
    session_id: str = Field(..., description="Onboarding session ID")
    partner_ids: List[str] = Field(..., min_items=1, max_items=10, description="Selected partner IDs")
    custom_partners: Optional[List[str]] = Field(None, max_items=5, description="Custom partner names")
    
    @validator('custom_partners')
    def validate_custom_partners(cls, v):
        """Validate custom partner names."""
        if v:
            return [name.strip() for name in v if name.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "partner_ids": ["partner-1", "partner-2"],
                "custom_partners": ["Board of Directors"]
            }
        }


class ConfigurePartnerSituationsRequest(BaseModel):
    """DTO for configuring situations for a specific partner."""
    session_id: str = Field(..., description="Onboarding session ID")
    partner_id: str = Field(..., description="Communication partner ID")
    unit_ids: List[str] = Field(..., min_items=1, max_items=20, description="Selected unit/situation IDs")
    custom_units: Optional[List[str]] = Field(None, max_items=10, description="Custom situation descriptions")
    
    @validator('custom_units')
    def validate_custom_units(cls, v):
        """Validate custom unit descriptions."""
        if v:
            return [desc.strip() for desc in v if desc.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "partner_id": "partner-1",
                "unit_ids": ["unit-1", "unit-2"],
                "custom_units": ["Quarterly planning meetings"]
            }
        }


class CompleteOnboardingRequest(BaseModel):
    """DTO for completing the onboarding process."""
    session_id: str = Field(..., description="Onboarding session ID")
    feedback: Optional[str] = Field(None, max_length=1000, description="Optional user feedback")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "feedback": "The onboarding process was smooth and intuitive"
            }
        }


class SkipOnboardingStepRequest(BaseModel):
    """DTO for skipping an onboarding step."""
    session_id: str = Field(..., description="Onboarding session ID")
    step: str = Field(..., description="Step to skip")
    reason: Optional[str] = Field(None, description="Reason for skipping")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "step": "role_selection",
                "reason": "Will configure later"
            }
        }