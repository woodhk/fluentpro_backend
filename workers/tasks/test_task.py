"""
Test task for verifying retry behavior
"""
import random
from celery.utils.log import get_task_logger
from workers.celery_app import app
from workers.tasks.base_task import BaseTask

logger = get_task_logger(__name__)


@app.task(bind=True, base=BaseTask)
def test_retry_task(self, fail_probability: float = 0.7):
    """
    Test task that randomly fails to demonstrate retry behavior
    
    Args:
        fail_probability: Probability of failure (0.0 to 1.0)
    """
    logger.info(f"Executing test_retry_task with fail_probability={fail_probability}")
    
    # Simulate random failure
    if random.random() < fail_probability:
        error_msg = f"Simulated failure (attempt {self.request.retries + 1})"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    result = {"status": "success", "attempt": self.request.retries + 1}
    logger.info(f"Task succeeded on attempt {self.request.retries + 1}")
    return result


@app.task(bind=True, base=BaseTask)
def test_deterministic_failure_task(self, success_on_attempt: int = 3):
    """
    Test task that succeeds only on a specific attempt number
    
    Args:
        success_on_attempt: Attempt number on which the task should succeed
    """
    current_attempt = self.request.retries + 1
    logger.info(f"Executing test_deterministic_failure_task (attempt {current_attempt})")
    
    if current_attempt < success_on_attempt:
        error_msg = f"Intentional failure on attempt {current_attempt} (will succeed on attempt {success_on_attempt})"
        logger.warning(error_msg)
        raise Exception(error_msg)
    
    result = {
        "status": "success", 
        "succeeded_on_attempt": current_attempt,
        "total_retries": self.request.retries
    }
    logger.info(f"Task succeeded on attempt {current_attempt} after {self.request.retries} retries")
    return result


@app.task(bind=True, base=BaseTask)
def test_always_fail_task(self):
    """
    Test task that always fails to verify max retry behavior
    """
    current_attempt = self.request.retries + 1
    error_msg = f"This task always fails (attempt {current_attempt})"
    logger.error(error_msg)
    raise Exception(error_msg)