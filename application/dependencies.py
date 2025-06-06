"""
Service Dependencies Registration

This module contains service registrations for the FluentPro application.
Services will be registered here as the refactoring progresses.

Current Status: Step 3 - ServiceRegistry refactored to use DI container
"""

from .container import get_container


def register_dependencies():
    """
    Register application dependencies with the DI container.
    
    Step 3 Status: ServiceRegistry now delegates to DI container.
    Services will be registered here as refactoring progresses through:
    - Step 4: Create interfaces for all services  
    - Step 5: Update managers to accept injected dependencies
    - Day 6-7: Implement Use Case Layer
    - Day 8-9: Standardize Service Layer
    """
    container = get_container()
    
    # No services to register yet - will be added as refactoring progresses
    print("DI Container: Step 3 complete - ServiceRegistry now uses DI container")


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