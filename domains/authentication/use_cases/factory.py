"""
Authentication use case factory.

Provides dependency injection for authentication use cases.
"""

from dependency_injector import containers, providers

from domains.authentication.use_cases.authenticate_user import AuthenticateUserUseCase
from domains.authentication.use_cases.register_user import RegisterUserUseCase


class AuthenticationUseCaseContainer(containers.DeclarativeContainer):
    """Container for authentication use cases with dependency injection."""
    
    # Dependencies
    user_repository = providers.Dependency()
    role_repository = providers.Dependency()
    auth_service = providers.Dependency()
    
    # Use cases
    authenticate_user = providers.Factory(
        AuthenticateUserUseCase,
        auth_service=auth_service,
        user_repository=user_repository
    )
    
    register_user = providers.Factory(
        RegisterUserUseCase,
        auth_service=auth_service,
        user_repository=user_repository
    )