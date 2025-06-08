"""
Celery configuration settings
"""
import os
from decouple import config

# Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery settings
broker_url = REDIS_URL
result_backend = REDIS_URL

# Task configuration
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task routing
task_routes = {
    'domains.authentication.tasks.*': {'queue': 'auth'},
    'domains.onboarding.tasks.*': {'queue': 'onboarding'},
    'workers.tasks.*': {'queue': 'default'},
}

# Worker configuration
worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000

# Task time limits
task_soft_time_limit = 300  # 5 minutes
task_time_limit = 600  # 10 minutes

# Result backend settings
result_expires = 3600  # 1 hour

# Retry configuration
task_default_retry_delay = 60  # 1 minute
task_max_retries = 3