import redis
import json
from typing import Optional, Dict, Any
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class OnboardingRedisClient:
    """Redis client specifically for onboarding progress caching."""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.key_prefix = "onboarding:progress:"
        self.ttl = 86400  # 24 hours - reasonable for session-like data
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        try:
            if settings.REDIS_URL:
                # Use Redis URL from environment (production)
                client = redis.from_url(
                    settings.REDIS_URL, 
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                client.ping()
                logger.info("Redis connection established")
                return client
            else:
                # Try local Redis for development
                try:
                    client = redis.Redis(
                        host='localhost', 
                        port=6379, 
                        db=0, 
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5
                    )
                    client.ping()
                    logger.info("Local Redis connection established")
                    return client
                except (redis.ConnectionError, redis.TimeoutError):
                    logger.warning("Redis not available, using database only")
                    return None
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def get_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding progress from Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.key_prefix}{user_id}"
            data = self.redis_client.get(key)
            
            if data:
                logger.debug(f"Cache hit for user {user_id}")
                return json.loads(data)
            
            logger.debug(f"Cache miss for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Set onboarding progress in Redis cache with TTL."""
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.key_prefix}{user_id}"
            # Ensure datetime objects are converted to strings
            serializable_data = {
                k: v.isoformat() if hasattr(v, 'isoformat') else v 
                for k, v in progress_data.items()
            }
            data = json.dumps(serializable_data)
            
            result = self.redis_client.setex(key, self.ttl, data)
            logger.debug(f"Cached progress for user {user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete_progress(self, user_id: str) -> bool:
        """Delete onboarding progress from Redis cache."""
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.key_prefix}{user_id}"
            result = self.redis_client.delete(key)
            logger.debug(f"Deleted cache for user {user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def extend_ttl(self, user_id: str) -> bool:
        """Extend TTL for active users."""
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.key_prefix}{user_id}"
            result = self.redis_client.expire(key, self.ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False


# Global instance
onboarding_redis = OnboardingRedisClient()