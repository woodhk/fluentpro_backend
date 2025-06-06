"""
DEPRECATED: Legacy Service Registry - Use application.container instead

This module provides backward compatibility for the old ServiceRegistry pattern.
New code should use the DI container from application.container.

MIGRATION GUIDE:
- Replace ServiceRegistry.get_service() with container.resolve()
- Replace ServiceMixin with @inject decorator
- Use dependency injection in constructors instead of property access
"""

import warnings
from typing import Dict, Any, Optional, Type, TypeVar
import logging

# Import the new DI container
from application.container import get_container, DependencyResolutionError
from core.interfaces import (
    UserRepositoryInterface,
    RoleRepositoryInterface,
    IndustryRepositoryInterface,
    CommunicationRepositoryInterface,
    AuthServiceInterface,
    EmbeddingServiceInterface,
    SearchServiceInterface,
    LLMServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    UnitOfWorkInterface
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Issue deprecation warning when this module is imported
warnings.warn(
    "ServiceRegistry is deprecated. Use application.container.get_container() instead.",
    DeprecationWarning,
    stacklevel=2
)


class ServiceRegistry:
    """
    DEPRECATED: Legacy service registry - use application.container instead.
    
    This class now delegates to the new DI container for backward compatibility.
    """
    
    # Mapping of old service names to new interface types
    _service_type_mapping = {
        'user_repository': UserRepositoryInterface,
        'role_repository': RoleRepositoryInterface,
        'industry_repository': IndustryRepositoryInterface,
        'communication_repository': CommunicationRepositoryInterface,
        'auth_service': AuthServiceInterface,
        'embedding_service': EmbeddingServiceInterface,
        'search_service': SearchServiceInterface,
        'database_service': DatabaseServiceInterface,
        'unit_of_work': UnitOfWorkInterface,
        'cache_service': CacheServiceInterface
    }
    
    @classmethod
    def get_service(cls, service_name: str, **kwargs) -> Any:
        """
        DEPRECATED: Get service instance by name.
        
        This method now delegates to the new DI container.
        Use container.resolve(ServiceType) instead.
        """
        warnings.warn(
            f"ServiceRegistry.get_service('{service_name}') is deprecated. "
            "Use container.resolve(ServiceType) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if service_name not in cls._service_type_mapping:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_type = cls._service_type_mapping[service_name]
        container = get_container()
        
        try:
            return container.resolve(service_type)
        except DependencyResolutionError as e:
            logger.error(f"Failed to resolve service {service_name}: {str(e)}")
            raise RuntimeError(f"Service resolution failed: {str(e)}") from e
    
    @classmethod
    def _create_service(cls, service_name: str, **kwargs) -> Any:
        """DEPRECATED: Use DI container instead."""
        return cls.get_service(service_name, **kwargs)
    
    @classmethod
    def register_service(cls, service_name: str, service_class_path: str):
        """
        DEPRECATED: Register a new service implementation.
        Use application.dependencies.register_dependencies() instead.
        """
        warnings.warn(
            "ServiceRegistry.register_service() is deprecated. "
            "Use application.dependencies.register_dependencies() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # No-op for backward compatibility
        pass
    
    @classmethod
    def get_user_repository(cls, **kwargs) -> UserRepositoryInterface:
        """DEPRECATED: Use container.resolve(UserRepositoryInterface) instead."""
        return cls.get_service('user_repository', **kwargs)
    
    @classmethod
    def get_role_repository(cls, **kwargs) -> RoleRepositoryInterface:
        """DEPRECATED: Use container.resolve(RoleRepositoryInterface) instead."""
        return cls.get_service('role_repository', **kwargs)
    
    @classmethod
    def get_industry_repository(cls, **kwargs) -> IndustryRepositoryInterface:
        """DEPRECATED: Use container.resolve(IndustryRepositoryInterface) instead."""
        return cls.get_service('industry_repository', **kwargs)
    
    @classmethod
    def get_communication_repository(cls, **kwargs) -> CommunicationRepositoryInterface:
        """DEPRECATED: Use container.resolve(CommunicationRepositoryInterface) instead."""
        return cls.get_service('communication_repository', **kwargs)
    
    @classmethod
    def get_auth_service(cls, **kwargs) -> AuthServiceInterface:
        """DEPRECATED: Use container.resolve(AuthServiceInterface) instead."""
        return cls.get_service('auth_service', **kwargs)
    
    @classmethod
    def get_embedding_service(cls, **kwargs) -> EmbeddingServiceInterface:
        """DEPRECATED: Use container.resolve(EmbeddingServiceInterface) instead."""
        return cls.get_service('embedding_service', **kwargs)
    
    @classmethod
    def get_search_service(cls, **kwargs) -> SearchServiceInterface:
        """DEPRECATED: Use container.resolve(SearchServiceInterface) instead."""
        return cls.get_service('search_service', **kwargs)
    
    @classmethod
    def get_database_service(cls, **kwargs) -> DatabaseServiceInterface:
        """DEPRECATED: Use container.resolve(DatabaseServiceInterface) instead."""
        return cls.get_service('database_service', **kwargs)
    
    @classmethod
    def get_unit_of_work(cls, **kwargs) -> UnitOfWorkInterface:
        """DEPRECATED: Use container.resolve(UnitOfWorkInterface) instead."""
        return cls.get_service('unit_of_work', **kwargs)
    
    @classmethod
    def get_cache_service(cls, **kwargs) -> CacheServiceInterface:
        """DEPRECATED: Use container.resolve(CacheServiceInterface) instead."""
        return cls.get_service('cache_service', **kwargs)
    
    @classmethod
    def clear_cache(cls):
        """
        DEPRECATED: Clear all cached service instances.
        Use container.clear_scoped_services() instead.
        """
        warnings.warn(
            "ServiceRegistry.clear_cache() is deprecated. "
            "Use container.clear_scoped_services() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        container = get_container()
        container.clear_scoped_services()
    
    @classmethod
    def clear_service(cls, service_name: str):
        """DEPRECATED: No equivalent in new DI container."""
        warnings.warn(
            "ServiceRegistry.clear_service() is deprecated and has no equivalent in the new DI container.",
            DeprecationWarning,
            stacklevel=2
        )


class LegacyServiceContainer:
    """
    DEPRECATED: Legacy service container - use @inject decorator instead.
    
    This class provides backward compatibility for the old property-based
    service access pattern. New code should use dependency injection.
    
    MIGRATION EXAMPLE:
    
    OLD:
        class MyManager:
            def __init__(self):
                self.services = LegacyServiceContainer()
            
            def do_something(self):
                user = self.services.users.get_by_id(1)
    
    NEW:
        @inject
        def do_something(user_repo: UserRepositoryInterface):
            user = user_repo.get_by_id(1)
    """
    
    def __init__(self):
        warnings.warn(
            "LegacyServiceContainer is deprecated. Use @inject decorator instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._container = get_container()
    
    @property
    def users(self) -> UserRepositoryInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(UserRepositoryInterface)
    
    @property
    def roles(self) -> RoleRepositoryInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(RoleRepositoryInterface)
    
    @property
    def industries(self) -> IndustryRepositoryInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(IndustryRepositoryInterface)
    
    @property
    def communication(self) -> CommunicationRepositoryInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(CommunicationRepositoryInterface)
    
    @property
    def auth(self) -> AuthServiceInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(AuthServiceInterface)
    
    @property
    def embedding(self) -> EmbeddingServiceInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(EmbeddingServiceInterface)
    
    @property
    def search(self) -> SearchServiceInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(SearchServiceInterface)
    
    @property
    def database(self) -> DatabaseServiceInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(DatabaseServiceInterface)
    
    @property
    def unit_of_work(self) -> UnitOfWorkInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(UnitOfWorkInterface)
    
    @property
    def cache(self) -> CacheServiceInterface:
        """DEPRECATED: Use dependency injection instead."""
        return self._container.resolve(CacheServiceInterface)


# Backward compatibility alias
ServiceContainer = LegacyServiceContainer


class ServiceMixin:
    """
    DEPRECATED: Legacy service mixin - use @inject decorator instead.
    
    This mixin provides backward compatibility for the old property-based
    service access pattern. New code should use dependency injection.
    
    MIGRATION EXAMPLE:
    
    OLD:
        class MyView(ServiceMixin, APIView):
            def post(self, request):
                user = self.services.users.get_by_id(request.user.id)
    
    NEW:
        class MyView(APIView):
            @inject
            def post(self, request, user_repo: UserRepositoryInterface):
                user = user_repo.get_by_id(request.user.id)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            "ServiceMixin is deprecated. Use @inject decorator instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._services = LegacyServiceContainer()
    
    @property
    def services(self) -> LegacyServiceContainer:
        """DEPRECATED: Get service container."""
        return self._services


# DEPRECATED: Legacy service factory functions - use DI container instead

def get_user_repository() -> UserRepositoryInterface:
    """DEPRECATED: Use container.resolve(UserRepositoryInterface) instead."""
    warnings.warn(
        "get_user_repository() is deprecated. Use container.resolve(UserRepositoryInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(UserRepositoryInterface)


def get_role_repository() -> RoleRepositoryInterface:
    """DEPRECATED: Use container.resolve(RoleRepositoryInterface) instead."""
    warnings.warn(
        "get_role_repository() is deprecated. Use container.resolve(RoleRepositoryInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(RoleRepositoryInterface)


def get_industry_repository() -> IndustryRepositoryInterface:
    """DEPRECATED: Use container.resolve(IndustryRepositoryInterface) instead."""
    warnings.warn(
        "get_industry_repository() is deprecated. Use container.resolve(IndustryRepositoryInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(IndustryRepositoryInterface)


def get_communication_repository() -> CommunicationRepositoryInterface:
    """DEPRECATED: Use container.resolve(CommunicationRepositoryInterface) instead."""
    warnings.warn(
        "get_communication_repository() is deprecated. Use container.resolve(CommunicationRepositoryInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(CommunicationRepositoryInterface)


def get_auth_service() -> AuthServiceInterface:
    """DEPRECATED: Use container.resolve(AuthServiceInterface) instead."""
    warnings.warn(
        "get_auth_service() is deprecated. Use container.resolve(AuthServiceInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(AuthServiceInterface)


def get_embedding_service() -> EmbeddingServiceInterface:
    """DEPRECATED: Use container.resolve(EmbeddingServiceInterface) instead."""
    warnings.warn(
        "get_embedding_service() is deprecated. Use container.resolve(EmbeddingServiceInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(EmbeddingServiceInterface)


def get_search_service() -> SearchServiceInterface:
    """DEPRECATED: Use container.resolve(SearchServiceInterface) instead."""
    warnings.warn(
        "get_search_service() is deprecated. Use container.resolve(SearchServiceInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(SearchServiceInterface)


def get_database_service() -> DatabaseServiceInterface:
    """DEPRECATED: Use container.resolve(DatabaseServiceInterface) instead."""
    warnings.warn(
        "get_database_service() is deprecated. Use container.resolve(DatabaseServiceInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(DatabaseServiceInterface)


def get_unit_of_work() -> UnitOfWorkInterface:
    """DEPRECATED: Use container.resolve(UnitOfWorkInterface) instead."""
    warnings.warn(
        "get_unit_of_work() is deprecated. Use container.resolve(UnitOfWorkInterface) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_container().resolve(UnitOfWorkInterface)


class ServiceConfig:
    """
    DEPRECATED: Legacy service configuration - use application.dependencies instead.
    
    Configuration is now handled in application.dependencies.register_dependencies().
    """
    
    @classmethod
    def configure_for_environment(cls, environment: str):
        """DEPRECATED: Use application.dependencies.register_environment_dependencies() instead."""
        warnings.warn(
            "ServiceConfig.configure_for_environment() is deprecated. "
            "Use application.dependencies.register_environment_dependencies() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Delegate to new dependency registration
        from application.dependencies import register_environment_dependencies
        register_environment_dependencies()


# DEPRECATED: Configure for Django environment
def configure_services():
    """
    DEPRECATED: Configure services based on Django settings.
    
    Use application.dependencies.register_dependencies() instead.
    """
    warnings.warn(
        "configure_services() is deprecated. "
        "Use application.dependencies.register_dependencies() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to new dependency registration
    from application.dependencies import register_dependencies, register_environment_dependencies
    
    register_dependencies()
    register_environment_dependencies()
    
    logger.info("Services configured using new DI container (legacy compatibility mode)")


# Migration helpers
def migrate_to_di_container():
    """
    Helper function to assist with migration from ServiceRegistry to DI container.
    
    This function provides guidance on migrating existing code.
    """
    migration_guide = """
    MIGRATION GUIDE: ServiceRegistry → DI Container
    
    1. Replace ServiceRegistry usage:
       OLD: ServiceRegistry.get_user_repository()
       NEW: container.resolve(UserRepositoryInterface)
    
    2. Replace ServiceMixin:
       OLD: class MyView(ServiceMixin, APIView)
       NEW: class MyView(APIView) with @inject decorator
    
    3. Replace property access:
       OLD: self.services.users.get_by_id(1)
       NEW: Inject UserRepositoryInterface in constructor
    
    4. Update service registration:
       OLD: ServiceRegistry.register_service()
       NEW: Use application.dependencies.register_dependencies()
    
    5. Environment configuration:
       OLD: ServiceConfig.configure_for_environment()
       NEW: application.dependencies.register_environment_dependencies()
    
    For detailed examples, see the documentation.
    """
    
    print(migration_guide)
    return migration_guide