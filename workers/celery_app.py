"""
Celery application configuration
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')

# Create the Celery application instance
app = Celery('fluentpro_backend')

# Load configuration from Django settings and Celery config
app.config_from_object('workers.celery_config', namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all Django apps
app.autodiscover_tasks()

# Import domain-specific tasks to ensure registration
try:
    # Import authentication tasks
    from domains.authentication.tasks import send_welcome_email, send_password_reset_email
    
    # Import onboarding tasks  
    from domains.onboarding.tasks import generate_user_recommendations, analyze_onboarding_completion
    
    # Import worker tasks
    from workers.tasks import test_task
    
except ImportError as e:
    # Tasks will be discovered during Django app loading
    pass

# Optional: Add debugging task
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')