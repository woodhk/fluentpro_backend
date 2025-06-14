"""Schemas for Onboarding Part 3 - Summary and Completion"""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from ..base import BaseResponse
from ...models.enums import NativeLanguage


class RoleSummary(BaseModel):
    """Summary of user's selected or custom role."""

    id: Optional[UUID] = None
    title: str
    description: str
    is_custom: bool
    industry_name: str

    model_config = ConfigDict(from_attributes=True)


class SituationSummary(BaseModel):
    """Summary of a communication situation/unit."""

    id: UUID
    name: str
    description: Optional[str] = None
    priority: int

    model_config = ConfigDict(from_attributes=True)


class CommunicationPartnerSummary(BaseModel):
    """Summary of a communication partner with their situations."""

    id: UUID
    name: str
    description: Optional[str] = None
    priority: int
    situations: List[SituationSummary]

    model_config = ConfigDict(from_attributes=True)


class OnboardingSummary(BaseModel):
    """Complete onboarding summary for a user."""

    # Basic info
    native_language: NativeLanguage
    native_language_display: str

    # Industry
    industry_id: Optional[UUID] = None
    industry_name: str

    # Role
    role: RoleSummary

    # Communication preferences
    communication_partners: List[CommunicationPartnerSummary]
    total_partners: int
    total_situations: int

    # Status
    onboarding_status: str
    is_complete: bool

    model_config = ConfigDict(from_attributes=True)


class OnboardingSummaryResponse(BaseResponse):
    """Response containing the onboarding summary."""

    summary: OnboardingSummary


class CompleteOnboardingResponse(BaseResponse):
    """Response for completing onboarding."""

    message: str
    onboarding_status: str
    next_steps: Optional[str] = None
