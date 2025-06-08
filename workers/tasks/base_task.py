"""
Base task class with common functionality
"""
from celery import Task
from celery.utils.log import get_task_logger
from typing import Any, Dict, Optional

logger = get_task_logger(__name__)


class BaseTask(Task):
    """
    Base task class with retry logic, error handling, and logging
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 300  # 5 minutes
    retry_jitter = True

    def __call__(self, *args, **kwargs):
        """Override call to add logging and context"""
        task_context = {
            'task_name': self.name,
            'task_id': getattr(self.request, 'id', 'unknown'),
            'retries': getattr(self.request, 'retries', 0),
            'args': args,
            'kwargs': kwargs
        }
        
        logger.info(f"Starting task: {self.name} (id: {task_context['task_id']}) "
                   f"with args: {args}, kwargs: {kwargs}")
        
        try:
            result = super().__call__(*args, **kwargs)
            logger.info(f"Task {self.name} (id: {task_context['task_id']}) completed successfully")
            return result
        except Exception as exc:
            logger.error(f"Task {self.name} (id: {task_context['task_id']}) failed with error: {exc}")
            raise

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Called when task is retried"""
        retry_count = getattr(self.request, 'retries', 0) + 1
        max_retries = getattr(self, 'max_retries', 3)
        logger.warning(
            f"Task {self.name} (id: {task_id}) retry attempt {retry_count}/{max_retries + 1} "
            f"due to: {exc}"
        )

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Called when task fails after all retries"""
        retry_count = getattr(self.request, 'retries', 0)
        logger.error(
            f"Task {self.name} (id: {task_id}) failed permanently after {retry_count} retries: {exc}"
        )

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called when task succeeds"""
        retry_count = getattr(self.request, 'retries', 0)
        if retry_count > 0:
            logger.info(
                f"Task {self.name} (id: {task_id}) succeeded after {retry_count} retries "
                f"with result: {retval}"
            )
        else:
            logger.info(f"Task {self.name} (id: {task_id}) succeeded on first attempt")


class CriticalTask(BaseTask):
    """
    Task class for critical operations with more aggressive retry settings
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 5, 'countdown': 30}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


class QuickTask(BaseTask):
    """
    Task class for quick operations with minimal retry
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 1, 'countdown': 10}
    retry_backoff = False
    retry_jitter = False