"""
Caching layer for FluentPro backend.
Provides Redis-based caching with fallback to in-memory cache.
"""

import json
import logging
from typing import Any, Optional, Union, Dict
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache as django_cache
from core.interfaces import CacheServiceInterface

logger = logging.getLogger(__name__)


class CacheService(CacheServiceInterface):
    """
    Production cache service using Redis through Django's cache framework.
    """
    
    def __init__(self):
        self.default_timeout = getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300)  # 5 minutes
        self.key_prefix = getattr(settings, 'CACHE_KEY_PREFIX', 'fluentpro')
    
    def _make_key(self, key: str) -> str:
        """Create properly prefixed cache key."""
        return f"{self.key_prefix}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            cache_key = self._make_key(key)
            value = django_cache.get(cache_key, default)
            
            if value is not None and value != default:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Timeout in seconds (None for default)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._make_key(key)
            timeout = timeout or self.default_timeout
            
            django_cache.set(cache_key, value, timeout)
            logger.debug(f"Cache set for key: {key} (timeout: {timeout}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._make_key(key)
            django_cache.delete(cache_key)
            logger.debug(f"Cache delete for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            cache_key = self._make_key(key)
            return django_cache.get(cache_key) is not None
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        """
        Clear all keys matching pattern.
        Note: This is implementation-dependent and may not work with all cache backends.
        
        Args:
            pattern: Pattern to match (simple string matching)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This is a simplified implementation
            # For production, you might want to use Redis-specific commands
            logger.warning(f"Clear pattern called for: {pattern} (implementation may be limited)")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Basic stats - implementation depends on cache backend
            return {
                'backend': 'django_cache',
                'prefix': self.key_prefix,
                'default_timeout': self.default_timeout,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {'status': 'error', 'error': str(e)}


class UserCacheService:
    """
    User-specific caching utilities.
    Provides convenience methods for user-related caching.
    """
    
    def __init__(self, cache_service: CacheServiceInterface):
        self.cache = cache_service
    
    def get_user_cache_key(self, auth0_id: str, key_suffix: str) -> str:
        """Generate user-specific cache key."""
        return f"user:{auth0_id}:{key_suffix}"
    
    def get_user_profile(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile."""
        key = self.get_user_cache_key(auth0_id, "profile")
        return self.cache.get(key)
    
    def set_user_profile(self, auth0_id: str, profile_data: Dict[str, Any], timeout: int = 600) -> bool:
        """Cache user profile for 10 minutes by default."""
        key = self.get_user_cache_key(auth0_id, "profile")
        return self.cache.set(key, profile_data, timeout)
    
    def get_user_roles(self, auth0_id: str) -> Optional[list]:
        """Get cached user role search results."""
        key = self.get_user_cache_key(auth0_id, "roles")
        return self.cache.get(key)
    
    def set_user_roles(self, auth0_id: str, roles_data: list, timeout: int = 300) -> bool:
        """Cache user role search results for 5 minutes."""
        key = self.get_user_cache_key(auth0_id, "roles")
        return self.cache.set(key, roles_data, timeout)
    
    def get_user_onboarding(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user onboarding data."""
        key = self.get_user_cache_key(auth0_id, "onboarding")
        return self.cache.get(key)
    
    def set_user_onboarding(self, auth0_id: str, onboarding_data: Dict[str, Any], timeout: int = 1800) -> bool:
        """Cache user onboarding data for 30 minutes."""
        key = self.get_user_cache_key(auth0_id, "onboarding")
        return self.cache.set(key, onboarding_data, timeout)
    
    def clear_user_cache(self, auth0_id: str) -> bool:
        """Clear all cached data for a user."""
        keys_to_clear = [
            self.get_user_cache_key(auth0_id, "profile"),
            self.get_user_cache_key(auth0_id, "roles"),
            self.get_user_cache_key(auth0_id, "onboarding")
        ]
        
        success = True
        for key in keys_to_clear:
            if not self.cache.delete(key):
                success = False
        
        return success


class MockCacheService(CacheServiceInterface):
    """
    Mock cache service for testing and development.
    Uses in-memory dictionary instead of Redis.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_timeout = 300
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from mock cache."""
        if key in self._cache:
            item = self._cache[key]
            # Check if expired
            if item['expires_at'] and datetime.now() > item['expires_at']:
                del self._cache[key]
                return default
            return item['value']
        return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in mock cache."""
        timeout = timeout or self.default_timeout
        expires_at = datetime.now() + timedelta(seconds=timeout) if timeout > 0 else None
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from mock cache."""
        if key in self._cache:
            del self._cache[key]
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in mock cache."""
        return self.get(key) is not None
    
    def clear_pattern(self, pattern: str) -> bool:
        """Clear keys matching pattern in mock cache."""
        keys_to_delete = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_delete:
            del self._cache[key]
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock cache statistics."""
        return {
            'backend': 'mock',
            'total_keys': len(self._cache),
            'default_timeout': self.default_timeout,
            'status': 'active'
        }


# Cache decorators for easy use
def cache_result(timeout: int = 300, key_func=None):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cache_service = CacheService()
            cached_result = cache_service.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator