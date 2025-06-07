"""Onboarding domain DTOs."""

from .requests import (
    StartOnboardingRequest,
    SelectLanguageRequest,
    SelectIndustryRequest,
    SelectRoleRequest,
    RoleDescriptionMatchRequest,
    SelectCommunicationPartnersRequest,
    ConfigurePartnerSituationsRequest,
    CompleteOnboardingRequest,
    SkipOnboardingStepRequest,
    ProficiencyLevel
)

from .responses import (
    OnboardingSessionResponse,
    LanguageOption,
    IndustryOption,
    RoleOption,
    RoleMatchResponse,
    CommunicationPartnerOption,
    CommunicationUnitOption,
    OnboardingStepResponse,
    OnboardingSummaryResponse,
    OnboardingStep,
    OnboardingSessionStatus
)

from .mappers import (
    OnboardingSessionMapper,
    IndustryMapper,
    RoleMapper,
    CommunicationMapper,
    OnboardingSummaryMapper
)

__all__ = [
    # Requests
    'StartOnboardingRequest',
    'SelectLanguageRequest',
    'SelectIndustryRequest',
    'SelectRoleRequest',
    'RoleDescriptionMatchRequest',
    'SelectCommunicationPartnersRequest',
    'ConfigurePartnerSituationsRequest',
    'CompleteOnboardingRequest',
    'SkipOnboardingStepRequest',
    'ProficiencyLevel',
    # Responses
    'OnboardingSessionResponse',
    'LanguageOption',
    'IndustryOption',
    'RoleOption',
    'RoleMatchResponse',
    'CommunicationPartnerOption',
    'CommunicationUnitOption',
    'OnboardingStepResponse',
    'OnboardingSummaryResponse',
    'OnboardingStep',
    'OnboardingSessionStatus',
    # Mappers
    'OnboardingSessionMapper',
    'IndustryMapper',
    'RoleMapper',
    'CommunicationMapper',
    'OnboardingSummaryMapper',
]