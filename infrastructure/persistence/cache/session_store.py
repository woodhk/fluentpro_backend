"""
Session store abstraction and Redis implementation for persistent session management
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Represents session data with metadata"""
    session_id: str
    user_id: Optional[str]
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create session data from dictionary"""
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            data=data.get("data", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"])
        )

class ISessionStore(ABC):
    """Abstract interface for session storage"""
    
    @abstractmethod
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 3600
    ) -> SessionData:
        """Create a new session with TTL"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session by ID"""
        pass
    
    @abstractmethod
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: bool = True,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Update session data and optionally extend TTL"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    async def extend_session_ttl(
        self,
        session_id: str,
        ttl_seconds: int = 3600
    ) -> bool:
        """Extend session TTL"""
        pass
    
    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions, return count of cleaned sessions"""
        pass
    
    @abstractmethod
    async def get_session_count(self) -> int:
        """Get total number of active sessions"""
        pass

class RedisSessionStore(ISessionStore):
    """Redis-backed session store with TTL management"""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "session:"):
        """
        Initialize Redis session store
        
        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for session keys in Redis
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.user_sessions_key_prefix = "user_sessions:"
        
    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self.key_prefix}{session_id}"
    
    def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user sessions set"""
        return f"{self.user_sessions_key_prefix}{user_id}"
    
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 3600
    ) -> SessionData:
        """Create a new session with TTL"""
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl_seconds)
            
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                data=data or {},
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            
            # Store session data in Redis with TTL
            session_key = self._get_session_key(session_id)
            serialized_data = json.dumps(session_data.to_dict())
            
            await self.redis.setex(session_key, ttl_seconds, serialized_data)
            
            # If user_id provided, add to user sessions set
            if user_id:
                user_sessions_key = self._get_user_sessions_key(user_id)
                await self.redis.sadd(user_sessions_key, session_id)
                # Set TTL on user sessions set (longer than individual sessions)
                await self.redis.expire(user_sessions_key, ttl_seconds + 300)
            
            logger.info(f"Created session {session_id} for user {user_id} with TTL {ttl_seconds}s")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session by ID"""
        try:
            session_key = self._get_session_key(session_id)
            session_data = await self.redis.get(session_key)
            
            if not session_data:
                return None
            
            data_dict = json.loads(session_data)
            session = SessionData.from_dict(data_dict)
            
            # Check if session has expired (extra safety check)
            if datetime.utcnow() > session.expires_at:
                await self.delete_session(session_id)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: bool = True,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Update session data and optionally extend TTL"""
        try:
            # Get current session
            current_session = await self.get_session(session_id)
            if not current_session:
                return False
            
            # Update session data
            current_session.data.update(data)
            current_session.updated_at = datetime.utcnow()
            
            # Extend TTL if requested
            if extend_ttl:
                if ttl_seconds is None:
                    # Calculate remaining TTL or use default
                    remaining_ttl = (current_session.expires_at - datetime.utcnow()).total_seconds()
                    ttl_seconds = max(int(remaining_ttl), 3600)  # At least 1 hour
                
                current_session.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            
            # Store updated session
            session_key = self._get_session_key(session_id)
            serialized_data = json.dumps(current_session.to_dict())
            
            if extend_ttl:
                await self.redis.setex(session_key, ttl_seconds, serialized_data)
            else:
                await self.redis.set(session_key, serialized_data, keepttl=True)
            
            logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            # Get session to find user_id
            session = await self.get_session(session_id)
            
            # Delete session key
            session_key = self._get_session_key(session_id)
            result = await self.redis.delete(session_key)
            
            # Remove from user sessions set if applicable
            if session and session.user_id:
                user_sessions_key = self._get_user_sessions_key(session.user_id)
                await self.redis.srem(user_sessions_key, session_id)
            
            logger.info(f"Deleted session {session_id}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def extend_session_ttl(
        self,
        session_id: str,
        ttl_seconds: int = 3600
    ) -> bool:
        """Extend session TTL"""
        try:
            session_key = self._get_session_key(session_id)
            
            # Check if session exists
            exists = await self.redis.exists(session_key)
            if not exists:
                return False
            
            # Extend TTL
            result = await self.redis.expire(session_key, ttl_seconds)
            
            # Update expires_at in session data
            session = await self.get_session(session_id)
            if session:
                session.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                serialized_data = json.dumps(session.to_dict())
                await self.redis.setex(session_key, ttl_seconds, serialized_data)
            
            logger.debug(f"Extended TTL for session {session_id} by {ttl_seconds}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extend TTL for session {session_id}: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user"""
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_ids = await self.redis.smembers(user_sessions_key)
            
            sessions = []
            for session_id in session_ids:
                session_id_str = session_id.decode() if isinstance(session_id, bytes) else session_id
                session = await self.get_session(session_id_str)
                if session:
                    sessions.append(session)
                else:
                    # Clean up stale session ID from set
                    await self.redis.srem(user_sessions_key, session_id_str)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions, return count of cleaned sessions"""
        try:
            # Scan for session keys
            pattern = f"{self.key_prefix}*"
            cleaned_count = 0
            
            async for key in self.redis.scan_iter(match=pattern, count=100):
                key_str = key.decode() if isinstance(key, bytes) else key
                session_id = key_str[len(self.key_prefix):]
                
                # Check if session has expired
                session = await self.get_session(session_id)
                if session is None:
                    # Session was already cleaned up or expired
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise
    
    async def get_session_count(self) -> int:
        """Get total number of active sessions"""
        try:
            pattern = f"{self.key_prefix}*"
            count = 0
            
            async for _ in self.redis.scan_iter(match=pattern, count=100):
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            raise

class SessionStoreFactory:
    """Factory for creating session store instances"""
    
    @staticmethod
    def create_redis_session_store(
        redis_client: redis.Redis,
        key_prefix: str = "session:"
    ) -> RedisSessionStore:
        """Create Redis session store instance"""
        return RedisSessionStore(redis_client, key_prefix)
    
    @staticmethod
    async def create_with_connection(
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "session:"
    ) -> RedisSessionStore:
        """Create Redis session store with new connection"""
        redis_client = redis.from_url(redis_url)
        
        # Test connection
        try:
            await redis_client.ping()
            logger.info("Redis connection established for session store")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for session store: {e}")
            raise
        
        return RedisSessionStore(redis_client, key_prefix)