"""
Authentication domain tasks for user onboarding communications
"""
import time
from typing import Dict, Any
from celery.utils.log import get_task_logger

from workers.celery_app import app
from workers.tasks.base_task import BaseTask

logger = get_task_logger(__name__)


@app.task(bind=True, base=BaseTask, queue='auth')
def send_welcome_email(self, user_id: str, user_email: str, user_name: str = None) -> Dict[str, Any]:
    """
    Send welcome email to newly registered user
    
    Args:
        user_id: User's unique identifier
        user_email: User's email address
        user_name: User's display name (optional)
    
    Returns:
        Dict containing email sending result
    """
    logger.info(f"Preparing welcome email for user {user_id} ({user_email})")
    
    try:
        # Simulate email preparation
        email_data = {
            'to': user_email,
            'subject': f"Welcome to FluentPro{f', {user_name}' if user_name else ''}!",
            'template': 'welcome_email',
            'variables': {
                'user_id': user_id,
                'user_name': user_name or 'there',
                'activation_link': f"https://app.fluentpro.com/activate/{user_id}",
                'support_email': 'support@fluentpro.com'
            }
        }
        
        # Simulate email service call with potential failure
        logger.info(f"Sending welcome email to {user_email}")
        
        # Simulate network delay
        time.sleep(0.5)
        
        # Simulate occasional email service failures for retry testing
        import random
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Email service temporarily unavailable")
        
        # Simulate successful email sending
        result = {
            'status': 'sent',
            'user_id': user_id,
            'email': user_email,
            'message_id': f"msg_{user_id}_{int(time.time())}",
            'timestamp': time.time(),
            'attempt': self.request.retries + 1
        }
        
        logger.info(f"Welcome email sent successfully to {user_email} (message_id: {result['message_id']})")
        return result
        
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {user_email}: {exc}")
        raise


@app.task(bind=True, base=BaseTask, queue='auth')
def send_password_reset_email(self, user_id: str, user_email: str, reset_token: str) -> Dict[str, Any]:
    """
    Send password reset email to user
    
    Args:
        user_id: User's unique identifier
        user_email: User's email address
        reset_token: Password reset token
    
    Returns:
        Dict containing email sending result
    """
    logger.info(f"Preparing password reset email for user {user_id} ({user_email})")
    
    try:
        # Simulate email preparation
        email_data = {
            'to': user_email,
            'subject': 'Reset Your FluentPro Password',
            'template': 'password_reset_email',
            'variables': {
                'user_id': user_id,
                'reset_link': f"https://app.fluentpro.com/reset-password?token={reset_token}",
                'expiry_hours': 24,
                'support_email': 'support@fluentpro.com'
            }
        }
        
        # Simulate email service call
        logger.info(f"Sending password reset email to {user_email}")
        
        # Simulate network delay
        time.sleep(0.3)
        
        # Simulate occasional failures
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Password reset email service error")
        
        result = {
            'status': 'sent',
            'user_id': user_id,
            'email': user_email,
            'reset_token': reset_token,
            'message_id': f"reset_{user_id}_{int(time.time())}",
            'timestamp': time.time(),
            'attempt': self.request.retries + 1
        }
        
        logger.info(f"Password reset email sent successfully to {user_email}")
        return result
        
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {user_email}: {exc}")
        raise