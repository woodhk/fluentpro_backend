"""
Application Container for FluentPro Backend

Provides dependency injection using dependency-injector library
for managing service dependencies and use cases.
"""

from dependency_injector import containers, providers

from domains.authentication.use_cases.factory import AuthenticationUseCaseContainer
from domains.onboarding.use_cases.factory import OnboardingUseCaseContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container for dependency injection."""
    
    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=["domains.authentication.api.v1.views", "domains.onboarding.api.v1"]
    )
    
    # Core dependencies (these will be configured during setup)
    user_repository = providers.Dependency()
    role_repository = providers.Dependency()
    partner_repository = providers.Dependency()
    industry_repository = providers.Dependency()
    auth_service = providers.Dependency()
    onboarding_service = providers.Dependency()
    profile_service = providers.Dependency()
    
    # Use case containers
    auth_use_cases = providers.Container(
        AuthenticationUseCaseContainer,
        user_repository=user_repository,
        role_repository=role_repository,
        auth_service=auth_service
    )
    
    onboarding_use_cases = providers.Container(
        OnboardingUseCaseContainer,
        user_repository=user_repository,
        partner_repository=partner_repository,
        industry_repository=industry_repository,
        onboarding_service=onboarding_service,
        profile_service=profile_service
    )


# Create container instance
container = ApplicationContainer()