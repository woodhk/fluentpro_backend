"""
Redis-based distributed lock implementation for concurrent state updates.

Provides thread-safe operations across multiple server instances using Redis
as the coordination mechanism with timeout and deadlock prevention.
"""

import asyncio
import logging
import uuid
import time
from abc import ABC, abstractmethod
from typing import Optional, Any
from contextlib import asynccontextmanager
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when lock acquisition fails"""
    pass


class LockTimeoutError(Exception):
    """Raised when lock acquisition times out"""
    pass


class IDistributedLock(ABC):
    """Interface for distributed lock implementations"""
    
    @abstractmethod
    async def acquire(
        self,
        lock_key: str,
        ttl_seconds: int = 30,
        timeout_seconds: Optional[int] = None,
        retry_interval_ms: int = 100
    ) -> str:
        """
        Acquire a distributed lock
        
        Args:
            lock_key: Unique key for the lock
            ttl_seconds: Time to live for the lock (deadlock prevention)
            timeout_seconds: Maximum time to wait for lock acquisition
            retry_interval_ms: Interval between acquisition attempts
            
        Returns:
            Lock token for release verification
            
        Raises:
            LockAcquisitionError: If lock cannot be acquired
            LockTimeoutError: If acquisition times out
        """
        pass
    
    @abstractmethod
    async def release(self, lock_key: str, lock_token: str) -> bool:
        """
        Release a distributed lock
        
        Args:
            lock_key: Key of the lock to release
            lock_token: Token returned from acquire() for verification
            
        Returns:
            True if lock was successfully released
        """
        pass
    
    @abstractmethod
    async def extend_lock(
        self,
        lock_key: str,
        lock_token: str,
        ttl_seconds: int = 30
    ) -> bool:
        """
        Extend the TTL of an existing lock
        
        Args:
            lock_key: Key of the lock to extend
            lock_token: Token for verification
            ttl_seconds: New TTL in seconds
            
        Returns:
            True if lock TTL was extended
        """
        pass
    
    @abstractmethod
    async def is_locked(self, lock_key: str) -> bool:
        """
        Check if a lock exists
        
        Args:
            lock_key: Key to check
            
        Returns:
            True if lock exists
        """
        pass


class RedisDistributedLock(IDistributedLock):
    """Redis-based distributed lock with timeout and deadlock prevention"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "lock:",
        default_ttl: int = 30
    ):
        """
        Initialize Redis distributed lock
        
        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for lock keys
            default_ttl: Default TTL for locks in seconds
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        
        # Lua script for atomic lock release
        self.release_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        # Lua script for atomic lock extension
        self.extend_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
    
    def _get_lock_key(self, lock_key: str) -> str:
        """Get Redis key for lock"""
        return f"{self.key_prefix}{lock_key}"
    
    def _generate_lock_token(self) -> str:
        """Generate unique lock token"""
        return f"{uuid.uuid4().hex}:{int(time.time() * 1000)}"
    
    async def acquire(
        self,
        lock_key: str,
        ttl_seconds: int = 30,
        timeout_seconds: Optional[int] = None,
        retry_interval_ms: int = 100
    ) -> str:
        """
        Acquire a distributed lock using Redis SET with NX and EX
        
        Args:
            lock_key: Unique key for the lock
            ttl_seconds: Time to live for the lock (deadlock prevention)
            timeout_seconds: Maximum time to wait for lock acquisition
            retry_interval_ms: Interval between acquisition attempts
            
        Returns:
            Lock token for release verification
            
        Raises:
            LockAcquisitionError: If lock cannot be acquired
            LockTimeoutError: If acquisition times out
        """
        try:
            redis_key = self._get_lock_key(lock_key)
            lock_token = self._generate_lock_token()
            start_time = time.time()
            
            # Use default TTL if not specified
            if ttl_seconds <= 0:
                ttl_seconds = self.default_ttl
            
            logger.debug(f"Attempting to acquire lock {lock_key} with TTL {ttl_seconds}s")
            
            while True:
                # Try to acquire lock using SET with NX (not exists) and EX (expiration)
                result = await self.redis.set(
                    redis_key,
                    lock_token,
                    nx=True,  # Only set if key doesn't exist
                    ex=ttl_seconds  # Set expiration time
                )
                
                if result:
                    logger.info(f"Successfully acquired lock {lock_key} with token {lock_token[:8]}...")
                    return lock_token
                
                # Check timeout
                if timeout_seconds is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout_seconds:
                        raise LockTimeoutError(
                            f"Failed to acquire lock {lock_key} within {timeout_seconds}s"
                        )
                
                # Wait before retrying
                await asyncio.sleep(retry_interval_ms / 1000.0)
                
        except (LockTimeoutError, LockAcquisitionError):
            raise
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_key}: {e}")
            raise LockAcquisitionError(f"Lock acquisition failed: {e}")
    
    async def release(self, lock_key: str, lock_token: str) -> bool:
        """
        Release a distributed lock using Lua script for atomic operation
        
        Args:
            lock_key: Key of the lock to release
            lock_token: Token returned from acquire() for verification
            
        Returns:
            True if lock was successfully released
        """
        try:
            redis_key = self._get_lock_key(lock_key)
            
            # Use Lua script to atomically check token and delete if match
            result = await self.redis.eval(
                self.release_script,
                1,  # Number of keys
                redis_key,
                lock_token
            )
            
            if result == 1:
                logger.info(f"Successfully released lock {lock_key}")
                return True
            else:
                logger.warning(f"Failed to release lock {lock_key} - token mismatch or lock not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to release lock {lock_key}: {e}")
            return False
    
    async def extend_lock(
        self,
        lock_key: str,
        lock_token: str,
        ttl_seconds: int = 30
    ) -> bool:
        """
        Extend the TTL of an existing lock using Lua script
        
        Args:
            lock_key: Key of the lock to extend
            lock_token: Token for verification
            ttl_seconds: New TTL in seconds
            
        Returns:
            True if lock TTL was extended
        """
        try:
            redis_key = self._get_lock_key(lock_key)
            
            # Use Lua script to atomically check token and extend TTL
            result = await self.redis.eval(
                self.extend_script,
                1,  # Number of keys
                redis_key,
                lock_token,
                str(ttl_seconds)
            )
            
            if result == 1:
                logger.debug(f"Extended lock {lock_key} TTL to {ttl_seconds}s")
                return True
            else:
                logger.warning(f"Failed to extend lock {lock_key} - token mismatch or lock not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to extend lock {lock_key}: {e}")
            return False
    
    async def is_locked(self, lock_key: str) -> bool:
        """
        Check if a lock exists
        
        Args:
            lock_key: Key to check
            
        Returns:
            True if lock exists
        """
        try:
            redis_key = self._get_lock_key(lock_key)
            result = await self.redis.exists(redis_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check lock existence {lock_key}: {e}")
            return False
    
    async def get_lock_ttl(self, lock_key: str) -> int:
        """
        Get remaining TTL for a lock
        
        Args:
            lock_key: Key to check
            
        Returns:
            Remaining TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        try:
            redis_key = self._get_lock_key(lock_key)
            return await self.redis.ttl(redis_key)
            
        except Exception as e:
            logger.error(f"Failed to get lock TTL {lock_key}: {e}")
            return -2


class DistributedLockManager:
    """
    Context manager for distributed locks with automatic cleanup.
    
    Provides convenient async context manager interface for lock usage
    with automatic release on exit.
    """
    
    def __init__(
        self,
        lock_impl: IDistributedLock,
        lock_key: str,
        ttl_seconds: int = 30,
        timeout_seconds: Optional[int] = None,
        retry_interval_ms: int = 100,
        auto_extend: bool = False,
        extend_threshold: float = 0.5
    ):
        """
        Initialize distributed lock manager
        
        Args:
            lock_impl: Distributed lock implementation
            lock_key: Unique key for the lock
            ttl_seconds: Time to live for the lock
            timeout_seconds: Maximum time to wait for acquisition
            retry_interval_ms: Interval between acquisition attempts
            auto_extend: Whether to automatically extend lock before expiration
            extend_threshold: When to extend (e.g., 0.5 = extend at 50% of TTL)
        """
        self.lock_impl = lock_impl
        self.lock_key = lock_key
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.retry_interval_ms = retry_interval_ms
        self.auto_extend = auto_extend
        self.extend_threshold = extend_threshold
        
        self.lock_token: Optional[str] = None
        self._extend_task: Optional[asyncio.Task] = None
    
    async def __aenter__(self) -> "DistributedLockManager":
        """Acquire lock on context entry"""
        try:
            self.lock_token = await self.lock_impl.acquire(
                self.lock_key,
                self.ttl_seconds,
                self.timeout_seconds,
                self.retry_interval_ms
            )
            
            # Start auto-extend task if enabled
            if self.auto_extend and self.lock_token:
                self._extend_task = asyncio.create_task(self._auto_extend_loop())
            
            return self
            
        except Exception as e:
            logger.error(f"Failed to acquire lock in context manager: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock on context exit"""
        try:
            # Cancel auto-extend task
            if self._extend_task:
                self._extend_task.cancel()
                try:
                    await self._extend_task
                except asyncio.CancelledError:
                    pass
            
            # Release lock
            if self.lock_token:
                await self.lock_impl.release(self.lock_key, self.lock_token)
                self.lock_token = None
                
        except Exception as e:
            logger.error(f"Failed to release lock in context manager: {e}")
    
    async def _auto_extend_loop(self):
        """Auto-extend lock before it expires"""
        try:
            while self.lock_token:
                # Wait until extension threshold
                sleep_time = self.ttl_seconds * self.extend_threshold
                await asyncio.sleep(sleep_time)
                
                # Extend lock
                if self.lock_token:
                    success = await self.lock_impl.extend_lock(
                        self.lock_key,
                        self.lock_token,
                        self.ttl_seconds
                    )
                    if not success:
                        logger.warning(f"Failed to auto-extend lock {self.lock_key}")
                        break
                        
        except asyncio.CancelledError:
            logger.debug(f"Auto-extend cancelled for lock {self.lock_key}")
        except Exception as e:
            logger.error(f"Error in auto-extend loop for lock {self.lock_key}: {e}")


@asynccontextmanager
async def distributed_lock(
    lock_impl: IDistributedLock,
    lock_key: str,
    ttl_seconds: int = 30,
    timeout_seconds: Optional[int] = None,
    retry_interval_ms: int = 100,
    auto_extend: bool = False,
    extend_threshold: float = 0.5
):
    """
    Async context manager for distributed locks
    
    Usage:
        async with distributed_lock(lock_impl, "my_lock", ttl_seconds=60) as lock_mgr:
            # Critical section protected by distributed lock
            await do_something()
    
    Args:
        lock_impl: Distributed lock implementation
        lock_key: Unique key for the lock
        ttl_seconds: Time to live for the lock
        timeout_seconds: Maximum time to wait for acquisition
        retry_interval_ms: Interval between acquisition attempts
        auto_extend: Whether to automatically extend lock before expiration
        extend_threshold: When to extend (e.g., 0.5 = extend at 50% of TTL)
        
    Yields:
        DistributedLockManager instance
    """
    lock_manager = DistributedLockManager(
        lock_impl=lock_impl,
        lock_key=lock_key,
        ttl_seconds=ttl_seconds,
        timeout_seconds=timeout_seconds,
        retry_interval_ms=retry_interval_ms,
        auto_extend=auto_extend,
        extend_threshold=extend_threshold
    )
    
    async with lock_manager:
        yield lock_manager


class DistributedLockFactory:
    """Factory for creating distributed lock instances"""
    
    @staticmethod
    def create_redis_lock(
        redis_client: redis.Redis,
        key_prefix: str = "lock:",
        default_ttl: int = 30
    ) -> RedisDistributedLock:
        """Create Redis distributed lock instance"""
        return RedisDistributedLock(
            redis_client=redis_client,
            key_prefix=key_prefix,
            default_ttl=default_ttl
        )
    
    @staticmethod
    async def create_with_connection(
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "lock:",
        default_ttl: int = 30
    ) -> RedisDistributedLock:
        """Create Redis distributed lock with new connection"""
        redis_client = redis.from_url(redis_url)
        
        # Test connection
        try:
            await redis_client.ping()
            logger.info("Redis connection established for distributed lock")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for distributed lock: {e}")
            raise
        
        return RedisDistributedLock(
            redis_client=redis_client,
            key_prefix=key_prefix,
            default_ttl=default_ttl
        )