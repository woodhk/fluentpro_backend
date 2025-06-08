"""
Async API testing utilities.
Provides utilities for testing asynchronous endpoints and operations.
"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable, List, Union, TypeVar, Coroutine
from contextlib import asynccontextmanager
from functools import wraps

import pytest
from django.test import AsyncClient as DjangoAsyncClient
from asgiref.sync import sync_to_async

from .api_client import JWTTestMixin


T = TypeVar('T')


class AsyncAPITestClient(DjangoAsyncClient, JWTTestMixin):
    """
    Async client for testing async API endpoints.
    Extends Django's AsyncClient with JWT authentication support.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_user = None
        self._current_token = None
    
    async def authenticate_as(
        self,
        user_id: str = 'test-user-123',
        email: str = 'test@example.com',
        **jwt_kwargs
    ) -> 'AsyncAPITestClient':
        """
        Authenticate the client as a specific user.
        
        Args:
            user_id: User ID for authentication
            email: User email
            **jwt_kwargs: Additional arguments for JWT creation
            
        Returns:
            Self for method chaining
        """
        self._current_user = {'id': user_id, 'email': email}
        self._current_token = self.create_test_jwt(user_id, email, **jwt_kwargs)
        
        # Set authorization header
        self.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self._current_token}'
        return self
    
    async def unauthenticate(self) -> 'AsyncAPITestClient':
        """Remove authentication from the client."""
        self._current_user = None
        self._current_token = None
        self.defaults.pop('HTTP_AUTHORIZATION', None)
        return self
    
    async def json_request(
        self,
        method: str,
        path: str,
        data: Optional[Union[Dict, List]] = None,
        **kwargs
    ) -> Any:
        """
        Make an async JSON request.
        
        Args:
            method: HTTP method
            path: Request path
            data: JSON data to send
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        kwargs.setdefault('content_type', 'application/json')
        
        if data is not None:
            kwargs['data'] = json.dumps(data)
        
        method_func = getattr(self, method.lower())
        return await method_func(path, **kwargs)
    
    async def parallel_requests(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Execute multiple requests in parallel.
        
        Args:
            requests: List of request configurations
                Each dict should have 'method', 'path', and optional kwargs
                
        Returns:
            List of responses in the same order
        """
        async def make_request(config):
            method = config.pop('method')
            path = config.pop('path')
            return await self.json_request(method, path, **config)
        
        return await asyncio.gather(*[make_request(req.copy()) for req in requests])


class AsyncTestTimer:
    """Utility for timing async operations in tests."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: Optional[float] = None
    
    async def __aenter__(self):
        """Start timing."""
        self.start_time = asyncio.get_event_loop().time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and calculate elapsed time."""
        self.end_time = asyncio.get_event_loop().time()
        self.elapsed = self.end_time - self.start_time
    
    def assert_faster_than(self, seconds: float):
        """Assert the operation completed within the specified time."""
        if self.elapsed is None:
            raise RuntimeError("Timer not used in context manager")
        assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
    
    def assert_slower_than(self, seconds: float):
        """Assert the operation took at least the specified time."""
        if self.elapsed is None:
            raise RuntimeError("Timer not used in context manager")
        assert self.elapsed >= seconds, f"Operation took {self.elapsed:.3f}s, expected >= {seconds}s"


class AsyncTestHelpers:
    """Collection of async test helper utilities."""
    
    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], Union[bool, Coroutine[Any, Any, bool]]],
        timeout: float = 5.0,
        poll_interval: float = 0.1,
        error_message: str = "Condition not met within timeout"
    ) -> None:
        """
        Wait for a condition to become true.
        
        Args:
            condition: Callable that returns bool (can be async)
            timeout: Maximum wait time in seconds
            poll_interval: Time between condition checks
            error_message: Error message if timeout reached
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check condition
            if asyncio.iscoroutinefunction(condition):
                result = await condition()
            else:
                result = condition()
            
            if result:
                return
            
            # Wait before next check
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(error_message)
    
    @staticmethod
    async def run_with_timeout(
        coro: Coroutine[Any, Any, T],
        timeout: float,
        timeout_error: str = "Operation timed out"
    ) -> T:
        """
        Run a coroutine with a timeout.
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            timeout_error: Error message on timeout
            
        Returns:
            Result of the coroutine
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(timeout_error)
    
    @staticmethod
    async def gather_with_errors(
        *coros: Coroutine[Any, Any, Any],
        return_exceptions: bool = True
    ) -> List[Union[Any, Exception]]:
        """
        Gather multiple coroutines, capturing exceptions.
        
        Args:
            *coros: Coroutines to run
            return_exceptions: If True, exceptions are returned in results
            
        Returns:
            List of results or exceptions
        """
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)
    
    @staticmethod
    @asynccontextmanager
    async def assert_max_duration(seconds: float):
        """
        Context manager that asserts code block completes within duration.
        
        Args:
            seconds: Maximum allowed duration
        """
        timer = AsyncTestTimer()
        async with timer:
            yield
        timer.assert_faster_than(seconds)
    
    @staticmethod
    async def retry_async(
        func: Callable[[], Coroutine[Any, Any, T]],
        max_attempts: int = 3,
        delay: float = 0.1,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> T:
        """
        Retry an async function with exponential backoff.
        
        Args:
            func: Async function to retry
            max_attempts: Maximum number of attempts
            delay: Initial delay between attempts
            backoff: Backoff multiplier
            exceptions: Tuple of exceptions to catch
            
        Returns:
            Result of the function
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                
                if attempt < max_attempts - 1:
                    wait_time = delay * (backoff ** attempt)
                    await asyncio.sleep(wait_time)
        
        raise last_exception


def async_test_with_timeout(timeout: float = 30.0):
    """
    Decorator for async tests with automatic timeout.
    
    Args:
        timeout: Test timeout in seconds
    """
    def decorator(test_func):
        @wraps(test_func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    test_func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                pytest.fail(f"Test timed out after {timeout} seconds")
        
        return wrapper
    return decorator


class AsyncDatabaseTestCase:
    """Mixin for async database operations in tests."""
    
    @staticmethod
    async def create_test_user(**kwargs):
        """Create a test user asynchronously."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        defaults.update(kwargs)
        
        return await sync_to_async(User.objects.create_user)(**defaults)
    
    @staticmethod
    async def count_model_instances(model_class):
        """Count instances of a model asynchronously."""
        return await sync_to_async(model_class.objects.count)()
    
    @staticmethod
    async def assert_model_exists(model_class, **filters):
        """Assert a model instance exists with given filters."""
        exists = await sync_to_async(model_class.objects.filter(**filters).exists)()
        assert exists, f"No {model_class.__name__} found with filters: {filters}"
    
    @staticmethod
    async def assert_model_count(model_class, expected_count: int):
        """Assert the count of model instances."""
        count = await sync_to_async(model_class.objects.count)()
        assert count == expected_count, f"Expected {expected_count} {model_class.__name__} instances, found {count}"


# Factory functions
def create_async_api_client(**auth_kwargs) -> AsyncAPITestClient:
    """
    Factory function to create an async API client.
    
    Args:
        **auth_kwargs: Arguments for authentication
        
    Returns:
        Configured AsyncAPITestClient
    """
    client = AsyncAPITestClient()
    
    async def setup():
        if auth_kwargs:
            await client.authenticate_as(**auth_kwargs)
        return client
    
    # Return a coroutine that sets up the client
    return setup()


# Export commonly used utilities
__all__ = [
    'AsyncAPITestClient',
    'AsyncTestTimer',
    'AsyncTestHelpers',
    'AsyncDatabaseTestCase',
    'async_test_with_timeout',
    'create_async_api_client',
]