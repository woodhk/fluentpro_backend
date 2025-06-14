from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
from typing import Optional
import os


# Redis connection for rate limiting
def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for rate limiting"""
    try:
        # For Render, check if Redis URL is provided
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis.from_url(redis_url, decode_responses=True)

        # For local development, try local Redis
        try:
            client = redis.Redis(
                host="localhost", port=6379, db=0, decode_responses=True
            )
            client.ping()  # Test connection
            return client
        except (redis.ConnectionError, redis.TimeoutError):
            print(
                "Warning: Redis not available, falling back to in-memory rate limiting"
            )
            return None
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None


# Initialize rate limiter
redis_client = get_redis_client()

if redis_client:
    # Use Redis-based rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=f"redis://{redis_client.connection_pool.connection_kwargs.get('host', 'localhost')}:{redis_client.connection_pool.connection_kwargs.get('port', 6379)}",
    )
else:
    # Fallback to in-memory rate limiting
    limiter = Limiter(key_func=get_remote_address)


# Custom rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded responses"""
    retry_after = getattr(
        exc, "retry_after", 60
    )  # Default to 60 seconds if not available
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Limit: {exc.detail}",
            "retry_after": retry_after,
        },
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


# Rate limiting decorators for different endpoints
WEBHOOK_RATE_LIMIT = "10/minute"  # 10 requests per minute for webhooks
AUTH_RATE_LIMIT = "30/minute"  # 30 requests per minute for auth endpoints
API_RATE_LIMIT = "100/minute"  # 100 requests per minute for general API
STRICT_RATE_LIMIT = "5/minute"  # 5 requests per minute for sensitive operations
