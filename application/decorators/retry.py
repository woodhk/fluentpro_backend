import asyncio
import functools
import time
from typing import TypeVar, Callable, Any, Union
import logging
import inspect

logger = logging.getLogger(__name__)
T = TypeVar('T')

def retry(max_attempts: int = 3, backoff_seconds: float = 1.0, exponential: bool = True):
    """Retry decorator with exponential backoff for both sync and async functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = backoff_seconds * (2 ** attempt if exponential else 1)
                            logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                
                raise last_exception
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = backoff_seconds * (2 ** attempt if exponential else 1)
                            logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {wait_time}s..."
                            )
                            time.sleep(wait_time)
                        else:
                            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                
                raise last_exception
            return sync_wrapper
    return decorator


def celery_retry_on_failure(max_retries: int = 3, countdown: int = 60, exponential: bool = True):
    """
    Celery-specific retry decorator that integrates with Celery's retry mechanism
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> T:
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                # Calculate countdown for exponential backoff
                current_retries = getattr(self.request, 'retries', 0)
                if exponential:
                    retry_countdown = countdown * (2 ** current_retries)
                else:
                    retry_countdown = countdown
                
                logger.warning(
                    f"Task {self.name} failed on attempt {current_retries + 1}: {exc}. "
                    f"Retrying in {retry_countdown}s..."
                )
                
                # Use Celery's built-in retry mechanism
                raise self.retry(
                    exc=exc,
                    countdown=retry_countdown,
                    max_retries=max_retries
                )
        return wrapper
    return decorator