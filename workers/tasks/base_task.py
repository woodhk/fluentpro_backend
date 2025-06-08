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
        """Override call to add logging"""
        logger.info(f"Starting task: {self.name} with args: {args}, kwargs: {kwargs}")
        try:
            result = super().__call__(*args, **kwargs)
            logger.info(f"Task {self.name} completed successfully")
            return result
        except Exception as exc:
            logger.error(f"Task {self.name} failed with error: {exc}")
            raise

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Called when task is retried"""
        logger.warning(f"Task {self.name} (id: {task_id}) retry attempt {self.request.retries + 1}")

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Called when task fails after all retries"""
        logger.error(f"Task {self.name} (id: {task_id}) failed permanently: {exc}")

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called when task succeeds"""
        logger.info(f"Task {self.name} (id: {task_id}) succeeded with result: {retval}")