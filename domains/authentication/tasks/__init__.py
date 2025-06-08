# Import tasks to register them with Celery
from .send_welcome_email import send_welcome_email, send_password_reset_email

__all__ = [
    'send_welcome_email',
    'send_password_reset_email',
]