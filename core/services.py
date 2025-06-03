"""
Service registry for dependency management and service instantiation.
Implements singleton pattern and dependency injection for services.
"""

from typing import Dict, Any, Optional, Type, TypeVar
from abc import ABC, abstractmethod
import logging
from threading import Lock

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


class ServiceRegistry:
    """
    Central service registry implementing dependency injection.
    Manages service instances and their dependencies.
    """
    
    _instances: Dict[str, Any] = {}
    _lock = Lock()
    
    # Service configuration - maps interfaces to implementations
    _service_config: Dict[str, str] = {
        'user_repository': 'shared.repositories.user_repository.UserRepository',
        'role_repository': 'shared.repositories.role_repository.RoleRepository',
        'industry_repository': 'shared.repositories.industry_repository.IndustryRepository',
        'communication_repository': 'shared.repositories.communication_repository.CommunicationRepository',
        'auth_service': 'authentication.services.auth0_service.Auth0Service',
        'embedding_service': 'authentication.services.azure_openai_service.AzureOpenAIService',
        'search_service': 'authentication.services.azure_search_service.AzureSearchService',
        'database_service': 'authentication.services.supabase_service.SupabaseService',
        'unit_of_work': 'core.unit_of_work.SupabaseUnitOfWork',
        'cache_service': 'core.cache.CacheService'
    }
    
    @classmethod
    def get_service(cls, service_name: str, **kwargs) -> Any:
        """
        Get service instance by name. Creates singleton instances.
        
        Args:
            service_name: Name of the service to get
            **kwargs: Additional arguments for service instantiation
            
        Returns:
            Service instance
        """
        with cls._lock:
            if service_name not in cls._instances:
                cls._instances[service_name] = cls._create_service(service_name, **kwargs)
            
            return cls._instances[service_name]
    
    @classmethod
    def _create_service(cls, service_name: str, **kwargs) -> Any:
        """Create service instance from configuration."""
        if service_name not in cls._service_config:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_path = cls._service_config[service_name]
        module_path, class_name = service_path.rsplit('.', 1)
        
        try:
            module = __import__(module_path, fromlist=[class_name])
            service_class = getattr(module, class_name)
            return service_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create service {service_name}: {str(e)}")
            raise RuntimeError(f"Service creation failed: {str(e)}")
    
    @classmethod
    def register_service(cls, service_name: str, service_class_path: str):
        """Register a new service implementation."""
        cls._service_config[service_name] = service_class_path
    
    @classmethod
    def get_user_repository(cls, **kwargs) -> UserRepositoryInterface:
        """Get user repository instance."""
        return cls.get_service('user_repository', **kwargs)
    
    @classmethod
    def get_role_repository(cls, **kwargs) -> RoleRepositoryInterface:
        """Get role repository instance."""
        return cls.get_service('role_repository', **kwargs)
    
    @classmethod
    def get_industry_repository(cls, **kwargs) -> IndustryRepositoryInterface:
        """Get industry repository instance."""
        return cls.get_service('industry_repository', **kwargs)
    
    @classmethod
    def get_communication_repository(cls, **kwargs) -> CommunicationRepositoryInterface:
        """Get communication repository instance."""
        return cls.get_service('communication_repository', **kwargs)
    
    @classmethod
    def get_auth_service(cls, **kwargs) -> AuthServiceInterface:
        """Get authentication service instance."""
        return cls.get_service('auth_service', **kwargs)
    
    @classmethod
    def get_embedding_service(cls, **kwargs) -> EmbeddingServiceInterface:
        """Get embedding service instance."""
        return cls.get_service('embedding_service', **kwargs)
    
    @classmethod
    def get_search_service(cls, **kwargs) -> SearchServiceInterface:
        """Get search service instance."""
        return cls.get_service('search_service', **kwargs)
    
    @classmethod
    def get_database_service(cls, **kwargs) -> DatabaseServiceInterface:
        """Get database service instance."""
        return cls.get_service('database_service', **kwargs)
    
    @classmethod
    def get_unit_of_work(cls, **kwargs) -> UnitOfWorkInterface:
        """Get unit of work instance."""
        return cls.get_service('unit_of_work', **kwargs)
    
    @classmethod
    def get_cache_service(cls, **kwargs) -> CacheServiceInterface:
        """Get cache service instance."""
        return cls.get_service('cache_service', **kwargs)
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached service instances."""
        with cls._lock:
            cls._instances.clear()
    
    @classmethod
    def clear_service(cls, service_name: str):
        """Clear specific service from cache."""
        with cls._lock:
            if service_name in cls._instances:
                del cls._instances[service_name]


class ServiceContainer:
    """
    Dependency injection container for managing service dependencies.
    Provides a cleaner interface for service access in business logic.
    """
    
    def __init__(self):
        self._registry = ServiceRegistry
    
    @property
    def users(self) -> UserRepositoryInterface:
        """Get user repository."""
        return self._registry.get_user_repository()
    
    @property
    def roles(self) -> RoleRepositoryInterface:
        """Get role repository."""
        return self._registry.get_role_repository()
    
    @property
    def industries(self) -> IndustryRepositoryInterface:
        """Get industry repository."""
        return self._registry.get_industry_repository()
    
    @property
    def communication(self) -> CommunicationRepositoryInterface:
        """Get communication repository."""
        return self._registry.get_communication_repository()
    
    @property
    def auth(self) -> AuthServiceInterface:
        """Get authentication service."""
        return self._registry.get_auth_service()
    
    @property
    def embedding(self) -> EmbeddingServiceInterface:
        """Get embedding service."""
        return self._registry.get_embedding_service()
    
    @property
    def search(self) -> SearchServiceInterface:
        """Get search service."""
        return self._registry.get_search_service()
    
    @property
    def database(self) -> DatabaseServiceInterface:
        """Get database service."""
        return self._registry.get_database_service()
    
    @property
    def unit_of_work(self) -> UnitOfWorkInterface:
        """Get unit of work."""
        return self._registry.get_unit_of_work()
    
    @property
    def cache(self) -> CacheServiceInterface:
        """Get cache service."""
        return self._registry.get_cache_service()


class ServiceMixin:
    """
    Mixin to provide easy access to services in views and business logic.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._services = ServiceContainer()
    
    @property
    def services(self) -> ServiceContainer:
        """Get service container."""
        return self._services


# Service factory functions for common use cases
def get_user_repository() -> UserRepositoryInterface:
    """Get user repository instance."""
    return ServiceRegistry.get_user_repository()


def get_role_repository() -> RoleRepositoryInterface:
    """Get role repository instance."""
    return ServiceRegistry.get_role_repository()


def get_industry_repository() -> IndustryRepositoryInterface:
    """Get industry repository instance."""
    return ServiceRegistry.get_industry_repository()


def get_communication_repository() -> CommunicationRepositoryInterface:
    """Get communication repository instance."""
    return ServiceRegistry.get_communication_repository()


def get_auth_service() -> AuthServiceInterface:
    """Get authentication service instance."""
    return ServiceRegistry.get_auth_service()


def get_embedding_service() -> EmbeddingServiceInterface:
    """Get embedding service instance."""
    return ServiceRegistry.get_embedding_service()


def get_search_service() -> SearchServiceInterface:
    """Get search service instance."""
    return ServiceRegistry.get_search_service()


def get_database_service() -> DatabaseServiceInterface:
    """Get database service instance."""
    return ServiceRegistry.get_database_service()


def get_unit_of_work() -> UnitOfWorkInterface:
    """Get unit of work instance."""
    return ServiceRegistry.get_unit_of_work()


class ServiceConfig:
    """
    Configuration for services based on environment.
    """
    
    # Development configuration
    DEVELOPMENT = {
        'user_repository': 'shared.repositories.user_repository.UserRepository',
        'role_repository': 'shared.repositories.role_repository.RoleRepository',
        'industry_repository': 'shared.repositories.industry_repository.IndustryRepository',
        'communication_repository': 'shared.repositories.communication_repository.CommunicationRepository',
        'auth_service': 'authentication.services.auth0_service.Auth0Service',
        'embedding_service': 'authentication.services.azure_openai_service.AzureOpenAIService',
        'search_service': 'authentication.services.azure_search_service.AzureSearchService',
        'database_service': 'authentication.services.supabase_service.SupabaseService',
    }
    
    # Testing configuration with mocks
    TESTING = {
        'user_repository': 'tests.mocks.mock_user_repository.MockUserRepository',
        'role_repository': 'tests.mocks.mock_role_repository.MockRoleRepository',
        'industry_repository': 'tests.mocks.mock_industry_repository.MockIndustryRepository',
        'communication_repository': 'tests.mocks.mock_communication_repository.MockCommunicationRepository',
        'auth_service': 'tests.mocks.mock_auth_service.MockAuthService',
        'embedding_service': 'tests.mocks.mock_embedding_service.MockEmbeddingService',
        'search_service': 'tests.mocks.mock_search_service.MockSearchService',
        'database_service': 'tests.mocks.mock_database_service.MockDatabaseService',
    }
    
    # Production configuration (same as development for now)
    PRODUCTION = DEVELOPMENT.copy()
    
    @classmethod
    def configure_for_environment(cls, environment: str):
        """Configure service registry for specific environment."""
        config = getattr(cls, environment.upper(), cls.DEVELOPMENT)
        
        for service_name, service_class_path in config.items():
            ServiceRegistry.register_service(service_name, service_class_path)


# Configure for Django environment
def configure_services():
    """Configure services based on Django settings."""
    from django.conf import settings
    
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    ServiceConfig.configure_for_environment(environment)
    
    logger.info(f"Services configured for {environment} environment")