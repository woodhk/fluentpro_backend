"""
Retry Decorator

Provides automatic retry logic for transient failures.
"""

import asyncio
import functools
import logging
from typing import Type, Tuple, Optional, Callable

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_multiplier: float = 2.0
):
    """
    Retry decorator for handling transient failures.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_seconds: Initial backoff time in seconds
        exceptions: Tuple of exceptions to catch and retry
        backoff_multiplier: Multiplier for exponential backoff
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_backoff = backoff_seconds
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_backoff} seconds..."
                    )
                    await asyncio.sleep(current_backoff)
                    current_backoff *= backoff_multiplier
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_backoff = backoff_seconds
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {current_backoff} seconds..."
                    )
                    import time
                    time.sleep(current_backoff)
                    current_backoff *= backoff_multiplier
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator