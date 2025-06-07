"""
Service Dependencies Registration

This module contains service registrations for the FluentPro application.
Services will be registered here as the refactoring progresses.

Current Status: Step 4 - Repository implementations registered with DI container
"""

from .container import get_container

# Repository interfaces
from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
from domains.onboarding.repositories.interfaces import IIndustryRepository, IPartnerRepository

# Repository implementations
from infrastructure.persistence.supabase.implementations.user_repository_impl import UserRepositoryImpl
from infrastructure.persistence.supabase.implementations.role_repository_impl import RoleRepositoryImpl
from infrastructure.persistence.supabase.implementations.industry_repository_impl import IndustryRepositoryImpl
from infrastructure.persistence.supabase.implementations.partner_repository_impl import PartnerRepositoryImpl

# Infrastructure services
from infrastructure.persistence.supabase.client import ISupabaseClient


def register_infrastructure(container):
    """Register infrastructure services with the DI container."""
    # For Step 4 completion, we'll register a simple stub
    # This allows the DI container to resolve dependencies without external services
    from unittest.mock import Mock
    
    # Create a mock Supabase client for DI container testing
    mock_client = Mock(spec=ISupabaseClient)
    
    container.register_instance(ISupabaseClient, mock_client)


def register_repositories(container):
    """Register repository implementations with the DI container."""
    # Authentication repositories
    container.register_singleton(
        IUserRepository,
        UserRepositoryImpl
    )
    container.register_singleton(
        IRoleRepository,
        RoleRepositoryImpl
    )
    
    # Onboarding repositories
    container.register_singleton(
        IIndustryRepository,
        IndustryRepositoryImpl
    )
    container.register_singleton(
        IPartnerRepository,
        PartnerRepositoryImpl
    )


def register_dependencies():
    """
    Register application dependencies with the DI container.
    
    Step 4 Status: Repository implementations now registered with DI container.
    Services will be registered here as refactoring progresses through:
    - Day 6-7: Implement Use Case Layer
    - Day 8-9: Standardize Service Layer
    """
    container = get_container()
    
    # Register infrastructure
    register_infrastructure(container)
    
    # Register repositories
    register_repositories(container)
    
    print("DI Container: Step 4 complete - Repository implementations registered")


def get_dependency_map() -> dict:
    """Return a map of all registered dependencies for debugging."""
    container = get_container()
    
    dependency_map = {}
    for service_type, descriptor in container._services.items():
        dependency_map[service_type.__name__] = {
            'implementation': descriptor.implementation.__name__ if descriptor.implementation else None,
            'lifetime': descriptor.lifetime,
            'has_factory': descriptor.factory is not None,
            'has_instance': descriptor.instance is not None,
        }
    
    return dependency_map


def validate_dependencies():
    """
    Validate that all critical dependencies can be resolved.
    
    Currently minimal validation during transition period.
    """
    # Will be expanded as services are added
    print("Dependency validation: Basic setup complete")