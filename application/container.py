"""
Dependency Injection Container for FluentPro Backend

This module provides a centralized container for managing service dependencies,
implementing the Inversion of Control (IoC) pattern to enable loose coupling
and testability across the application.
"""

import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints
from functools import wraps

T = TypeVar('T')


class ServiceLifetime:
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DependencyResolutionError(Exception):
    """Raised when a dependency cannot be resolved."""
    pass


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""
    pass


class ServiceDescriptor:
    """Describes how a service should be instantiated and managed."""

    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: str = ServiceLifetime.TRANSIENT
    ):
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self._singleton_instance = None


class ServiceContainer:
    """
    Dependency Injection Container
    
    Manages service registration, resolution, and lifecycle.
    Supports constructor injection, factory functions, and singleton patterns.
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_services: Dict[Type, Any] = {}
        self._resolution_stack: list = []

    def register_singleton(self, service_type: Type[T], implementation: Optional[Type[T]] = None) -> 'ServiceContainer':
        """Register a service as singleton (one instance for application lifetime)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON
        )
        return self

    def register_transient(self, service_type: Type[T], implementation: Optional[Type[T]] = None) -> 'ServiceContainer':
        """Register a service as transient (new instance every time)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT
        )
        return self

    def register_scoped(self, service_type: Type[T], implementation: Optional[Type[T]] = None) -> 'ServiceContainer':
        """Register a service as scoped (one instance per request/scope)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SCOPED
        )
        return self

    def register_factory(self, service_type: Type[T], factory: Callable[[], T], lifetime: str = ServiceLifetime.TRANSIENT) -> 'ServiceContainer':
        """Register a service with a factory function."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceContainer':
        """Register a specific instance as singleton."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        descriptor._singleton_instance = instance
        self._services[service_type] = descriptor
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.
        
        Args:
            service_type: The type of service to resolve
            
        Returns:
            An instance of the requested service
            
        Raises:
            DependencyResolutionError: If the service cannot be resolved
            CircularDependencyError: If circular dependencies are detected
        """
        if service_type in self._resolution_stack:
            circular_path = " -> ".join([t.__name__ for t in self._resolution_stack])
            raise CircularDependencyError(
                f"Circular dependency detected: {circular_path} -> {service_type.__name__}"
            )

        if service_type not in self._services:
            raise DependencyResolutionError(f"Service {service_type.__name__} is not registered")

        descriptor = self._services[service_type]

        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor._singleton_instance is not None:
                return descriptor._singleton_instance

            instance = self._create_instance(descriptor)
            descriptor._singleton_instance = instance
            return instance

        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_services:
                return self._scoped_services[service_type]

            instance = self._create_instance(descriptor)
            self._scoped_services[service_type] = instance
            return instance

        else:  # TRANSIENT
            return self._create_instance(descriptor)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance based on the service descriptor."""
        try:
            self._resolution_stack.append(descriptor.service_type)

            # Use pre-registered instance
            if descriptor.instance is not None:
                return descriptor.instance

            # Use factory function
            if descriptor.factory is not None:
                return self._resolve_factory_dependencies(descriptor.factory)

            # Use constructor injection
            return self._resolve_constructor_dependencies(descriptor.implementation)

        finally:
            if descriptor.service_type in self._resolution_stack:
                self._resolution_stack.remove(descriptor.service_type)

    def _resolve_constructor_dependencies(self, implementation: Type) -> Any:
        """Resolve constructor dependencies and create instance."""
        try:
            # Get constructor signature
            signature = inspect.signature(implementation.__init__)
            type_hints = get_type_hints(implementation.__init__)

            # Resolve dependencies
            kwargs = {}
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue

                param_type = type_hints.get(param_name)
                if param_type is None:
                    if param.default is not inspect.Parameter.empty:
                        continue  # Skip optional parameters with defaults
                    raise DependencyResolutionError(
                        f"Cannot resolve parameter '{param_name}' for {implementation.__name__}: no type hint provided"
                    )

                kwargs[param_name] = self.resolve(param_type)

            return implementation(**kwargs)

        except Exception as e:
            raise DependencyResolutionError(
                f"Failed to create instance of {implementation.__name__}: {str(e)}"
            ) from e

    def _resolve_factory_dependencies(self, factory: Callable) -> Any:
        """Resolve factory function dependencies."""
        try:
            signature = inspect.signature(factory)
            type_hints = get_type_hints(factory)

            kwargs = {}
            for param_name, param in signature.parameters.items():
                param_type = type_hints.get(param_name)
                if param_type is None:
                    if param.default is not inspect.Parameter.empty:
                        continue
                    raise DependencyResolutionError(
                        f"Cannot resolve parameter '{param_name}' for factory function: no type hint provided"
                    )

                kwargs[param_name] = self.resolve(param_type)

            return factory(**kwargs)

        except Exception as e:
            raise DependencyResolutionError(f"Failed to execute factory function: {str(e)}") from e

    def clear_scoped_services(self):
        """Clear all scoped service instances (typically called at end of request)."""
        self._scoped_services.clear()

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services

    def get_registration_info(self, service_type: Type) -> Optional[ServiceDescriptor]:
        """Get registration information for a service type."""
        return self._services.get(service_type)


# Global container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container instance."""
    return _container


def inject(func: Callable) -> Callable:
    """
    Decorator for automatic dependency injection.
    
    Resolves function parameters from the service container based on type hints.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Resolve missing dependencies
        for param_name, param in signature.parameters.items():
            if param_name in kwargs:
                continue  # Already provided

            param_type = type_hints.get(param_name)
            if param_type and _container.is_registered(param_type):
                kwargs[param_name] = _container.resolve(param_type)

        return func(*args, **kwargs)

    return wrapper


class Injectable:
    """
    Base class for services that support automatic dependency injection.
    
    Services inheriting from this class will have their dependencies
    automatically resolved when instantiated through the container.
    """

    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses as transient services."""
        super().__init_subclass__(**kwargs)
        # Auto-registration can be enabled here if desired
        # _container.register_transient(cls)


# Context manager for scoped services (e.g., per-request scope)
class ServiceScope:
    """Context manager for scoped service lifetime management."""

    def __init__(self, container: ServiceContainer):
        self.container = container

    def __enter__(self):
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.clear_scoped_services()


# Utility functions
def create_scope() -> ServiceScope:
    """Create a new service scope (typically per request)."""
    return ServiceScope(_container)


def reset_container():
    """Reset the global container (useful for testing)."""
    global _container
    _container = ServiceContainer()


def list_registered_services():
    """List all registered services for debugging during refactoring."""
    container = get_container()
    
    if not container._services:
        print("No services registered yet")
        return
    
    print("Registered Services:")
    for service_type, descriptor in container._services.items():
        impl_name = descriptor.implementation.__name__ if descriptor.implementation else "None"
        print(f"  - {service_type.__name__} → {impl_name} ({descriptor.lifetime})")


def get_container_status():
    """Get container status for debugging during refactoring."""
    container = get_container()
    
    return {
        'total_services': len(container._services),
        'scoped_instances': len(container._scoped_services),
        'resolution_stack_depth': len(container._resolution_stack),
    }