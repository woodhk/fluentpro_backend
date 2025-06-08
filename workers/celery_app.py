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

# Optional: Add debugging task
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')