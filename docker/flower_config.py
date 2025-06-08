"""
Flower monitoring dashboard configuration
"""
import os

# Basic authentication
basic_auth = [os.getenv('FLOWER_BASIC_AUTH', 'admin:fluentpro123')]

# URL prefix (useful if behind reverse proxy)
url_prefix = os.getenv('FLOWER_URL_PREFIX', '')

# Auto-refresh interval in seconds
auto_refresh = True
refresh_interval = 5000  # 5 seconds

# Enable events monitoring
enable_events = True

# Maximum number of workers to display
max_workers = 10

# Task columns to display
tasks_columns = [
    'name', 'uuid', 'state', 'args', 'kwargs', 
    'result', 'received', 'started', 'runtime', 'worker'
]

# Worker columns to display  
workers_columns = [
    'name', 'status', 'active', 'processed', 'load_avg', 'pool'
]

# Monitoring settings
inspect_timeout = 10.0
stats_timeout = 10.0

# Logging configuration
logging = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'flower': {
            'handlers': ['console'],
            'level': os.getenv('FLOWER_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Security settings
xheaders = True  # Trust X-Real-IP headers from reverse proxy

# Database settings for persistent storage (optional)
# db = 'flower.db'  # Uncomment to enable persistent storage

# Custom dashboard title
title = 'FluentPro Celery Monitor'