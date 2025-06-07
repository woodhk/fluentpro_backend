import functools
import hashlib
import json
from typing import TypeVar, Callable, Any, Optional
from datetime import timedelta
from core.cache import CacheService

T = TypeVar('T')

def cache(key_prefix: str, ttl: timedelta = timedelta(minutes=5)):
    """Cache decorator with Django cache backend"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            cache_service = CacheService()
            cached_value = cache_service.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(
                cache_key,
                result,
                int(ttl.total_seconds())
            )
            
            return result
        
        return wrapper
    return decorator

def cache_sync(key_prefix: str, ttl: timedelta = timedelta(minutes=5)):
    """Cache decorator for synchronous functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            cache_service = CacheService()
            cached_value = cache_service.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(
                cache_key,
                result,
                int(ttl.total_seconds())
            )
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(key_pattern: str):
    """Invalidate cache entries matching pattern"""
    async def _invalidate():
        cache_service = CacheService()
        return cache_service.clear_pattern(key_pattern)
    return _invalidate

def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function arguments"""
    # Create a hash from args and kwargs for the key
    args_str = str(args) + str(sorted(kwargs.items()))
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
    return f"{prefix}:{func_name}:{args_hash}"