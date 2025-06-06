"""
Application Layer

This module provides the core application infrastructure including
dependency injection, middleware, decorators, and shared utilities.
"""

from .container import (
    get_container, 
    inject, 
    create_scope, 
    Injectable, 
    ServiceScope,
    list_registered_services,
    get_container_status
)
from .dependencies import register_dependencies

# Make key components easily importable
__all__ = [
    'get_container',
    'inject',
    'create_scope',
    'Injectable',
    'ServiceScope',
    'register_dependencies',
    'list_registered_services',
    'get_container_status',
]

# Auto-register dependencies when the application module is imported
def setup_application():
    """Initialize the application layer with default dependencies."""
    register_dependencies()

# You can choose to auto-setup on import or call it explicitly
# setup_application()  # Will be enabled when services are ready