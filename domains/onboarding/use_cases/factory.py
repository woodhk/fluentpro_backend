"""
Onboarding use case factory.

Provides dependency injection for onboarding use cases.
"""

from dependency_injector import containers, providers

from domains.onboarding.use_cases.start_onboarding_session import StartOnboardingSessionUseCase
from domains.onboarding.use_cases.complete_onboarding_flow import CompleteOnboardingFlowUseCase
from domains.onboarding.use_cases.select_communication_partners import SelectCommunicationPartnersUseCase
from domains.onboarding.use_cases.select_user_industry import SelectUserIndustry
from domains.onboarding.use_cases.select_native_language import SelectNativeLanguage
from domains.onboarding.use_cases.create_custom_user_role import CreateCustomUserRole
from domains.onboarding.use_cases.match_user_role_from_description import MatchUserRoleFromDescription
from domains.onboarding.use_cases.configure_partner_situations import ConfigurePartnerSituations


class OnboardingUseCaseContainer(containers.DeclarativeContainer):
    """Container for onboarding use cases with dependency injection."""
    
    # Dependencies
    user_repository = providers.Dependency()
    partner_repository = providers.Dependency()
    industry_repository = providers.Dependency()
    onboarding_service = providers.Dependency()
    profile_service = providers.Dependency()
    
    # Use cases
    start_onboarding_session = providers.Factory(
        StartOnboardingSessionUseCase,
        user_repository=user_repository
    )
    
    complete_onboarding_flow = providers.Factory(
        CompleteOnboardingFlowUseCase,
        user_repository=user_repository,
        partner_repository=partner_repository,
        onboarding_service=onboarding_service
    )
    
    select_communication_partners = providers.Factory(
        SelectCommunicationPartnersUseCase,
        partner_repository=partner_repository,
        user_repository=user_repository,
        profile_service=profile_service
    )
    
    select_user_industry = providers.Factory(
        SelectUserIndustry,
        user_repository=user_repository,
        industry_repository=industry_repository
    )
    
    select_native_language = providers.Factory(
        SelectNativeLanguage,
        user_repository=user_repository
    )
    
    create_custom_user_role = providers.Factory(
        CreateCustomUserRole,
        user_repository=user_repository
    )
    
    match_user_role_from_description = providers.Factory(
        MatchUserRoleFromDescription,
        user_repository=user_repository
    )
    
    configure_partner_situations = providers.Factory(
        ConfigurePartnerSituations,
        user_repository=user_repository,
        partner_repository=partner_repository
    )