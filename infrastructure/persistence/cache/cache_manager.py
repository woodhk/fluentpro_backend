"""
Cache abstraction layer for the application
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ICacheManager(ABC):
    """Interface for cache management operations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple key-value pairs"""
        pass
    
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values by keys"""
        pass
    
    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache (optionally by pattern)"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration for existing key"""
        pass

class RedisCacheManager(ICacheManager):
    """Redis-based cache manager implementation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", key_prefix: str = "cache:"):
        """
        Initialize Redis cache manager
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all cache keys
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis_pool = None
        self._redis = None
    
    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            self._redis_pool = redis.ConnectionPool.from_url(self.redis_url)
            self._redis = redis.Redis(connection_pool=self._redis_pool)
            
            # Test connection
            await self._redis.ping()
            logger.info("Redis cache manager connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
        if self._redis_pool:
            await self._redis_pool.disconnect()
        logger.info("Redis cache manager disconnected")
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        if isinstance(value, str):
            return value
        return json.dumps(value)
    
    def _deserialize_value(self, value: Optional[bytes]) -> Optional[Any]:
        """Deserialize value from storage"""
        if value is None:
            return None
        
        try:
            decoded = value.decode('utf-8')
            # Try to parse as JSON first
            try:
                return json.loads(decoded)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return decoded
        except UnicodeDecodeError:
            logger.warning("Failed to decode cache value as UTF-8")
            return None
    
    def _get_ttl_seconds(self, ttl: Optional[Union[int, timedelta]]) -> Optional[int]:
        """Convert TTL to seconds"""
        if ttl is None:
            return None
        if isinstance(ttl, timedelta):
            return int(ttl.total_seconds())
        return ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            redis_key = self._make_key(key)
            value = await self._redis.get(redis_key)
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value with optional TTL"""
        try:
            redis_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            ttl_seconds = self._get_ttl_seconds(ttl)
            
            result = await self._redis.set(redis_key, serialized_value, ex=ttl_seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            redis_key = self._make_key(key)
            result = await self._redis.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            redis_key = self._make_key(key)
            result = await self._redis.exists(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check existence of cache key {key}: {e}")
            return False
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple key-value pairs"""
        try:
            pipeline = self._redis.pipeline()
            ttl_seconds = self._get_ttl_seconds(ttl)
            
            for key, value in mapping.items():
                redis_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                pipeline.set(redis_key, serialized_value, ex=ttl_seconds)
            
            results = await pipeline.execute()
            return all(results)
        except Exception as e:
            logger.error(f"Failed to set multiple cache keys: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values by keys"""
        try:
            redis_keys = [self._make_key(key) for key in keys]
            values = await self._redis.mget(redis_keys)
            
            result = {}
            for i, key in enumerate(keys):
                result[key] = self._deserialize_value(values[i])
            
            return result
        except Exception as e:
            logger.error(f"Failed to get multiple cache keys: {e}")
            return {key: None for key in keys}
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys"""
        try:
            if not keys:
                return 0
            
            redis_keys = [self._make_key(key) for key in keys]
            result = await self._redis.delete(*redis_keys)
            return result
        except Exception as e:
            logger.error(f"Failed to delete multiple cache keys: {e}")
            return 0
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache (optionally by pattern)"""
        try:
            if pattern:
                redis_pattern = self._make_key(pattern)
            else:
                redis_pattern = f"{self.key_prefix}*"
            
            # Get all matching keys
            keys = []
            async for key in self._redis.scan_iter(match=redis_pattern):
                keys.append(key)
            
            if keys:
                result = await self._redis.delete(*keys)
                return result
            
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        try:
            redis_key = self._make_key(key)
            result = await self._redis.incrby(redis_key, amount)
            return result
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            raise
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration for existing key"""
        try:
            redis_key = self._make_key(key)
            ttl_seconds = self._get_ttl_seconds(ttl)
            if ttl_seconds is None:
                return False
            
            result = await self._redis.expire(redis_key, ttl_seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key in seconds"""
        try:
            redis_key = self._make_key(key)
            result = await self._redis.ttl(redis_key)
            return result if result >= 0 else None
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return None
    
    async def persist(self, key: str) -> bool:
        """Remove expiration from key"""
        try:
            redis_key = self._make_key(key)
            result = await self._redis.persist(redis_key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to persist cache key {key}: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        return self._redis is not None

class InMemoryCacheManager(ICacheManager):
    """Simple in-memory cache manager for testing/development"""
    
    def __init__(self):
        """Initialize in-memory cache"""
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
    
    def _is_expired(self, key: str) -> bool:
        """Check if key has expired"""
        if key not in self._expiry:
            return False
        
        import time
        return time.time() > self._expiry[key]
    
    def _cleanup_expired(self, key: str) -> None:
        """Remove expired key"""
        if self._is_expired(key):
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        self._cleanup_expired(key)
        return self._cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value with optional TTL"""
        self._cache[key] = value
        
        if ttl is not None:
            import time
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            self._expiry[key] = time.time() + ttl
        else:
            self._expiry.pop(key, None)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        existed = key in self._cache
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return existed
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        self._cleanup_expired(key)
        return key in self._cache
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple key-value pairs"""
        for key, value in mapping.items():
            await self.set(key, value, ttl)
        return True
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values by keys"""
        result = {}
        for key in keys:
            result[key] = await self.get(key)
        return result
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys"""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache (optionally by pattern)"""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            self._expiry.clear()
            return count
        
        # Simple pattern matching (only supports * wildcard)
        import fnmatch
        keys_to_delete = [
            key for key in self._cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        
        return await self.delete_many(keys_to_delete)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        current = await self.get(key)
        if current is None:
            current = 0
        elif not isinstance(current, (int, float)):
            raise ValueError(f"Cannot increment non-numeric value: {current}")
        
        new_value = current + amount
        await self.set(key, new_value)
        return new_value
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration for existing key"""
        if key not in self._cache:
            return False
        
        import time
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        
        self._expiry[key] = time.time() + ttl
        return True