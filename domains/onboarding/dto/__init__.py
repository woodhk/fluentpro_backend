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
    OnboardingStatus
)

from .mappers import (
    OnboardingSessionMapper,
    OnboardingStepMapper
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
    'OnboardingStatus',
    # Mappers
    'OnboardingSessionMapper',
    'OnboardingStepMapper',
]