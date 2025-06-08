"""
Staging-specific settings for FluentPro backend.
Production-like environment for pre-deployment testing.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Staging security settings (less strict than production for debugging)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Less restrictive than production

# Allow staging hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,staging.fluentpro.com', cast=Csv())

# Staging database (similar to production setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='fluentpro_staging'),
        'USER': config('DB_USER', default='fluentpro_staging'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'sslmode': config('DB_SSL_MODE', default='prefer'),
        }
    }
}

# WebSocket configuration for staging
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config('REDIS_URL', default='redis://127.0.0.1:6379/2')],
            "capacity": 1000,
            "expiry": 10,
        },
    },
}

# Static files configuration
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files configuration  
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# CORS configuration for staging
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', 
    default='https://staging-app.fluentpro.com,https://staging.fluentpro.com',
    cast=Csv()
)

# Logging configuration (more verbose than production for debugging)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('LOG_FILE_PATH', default='/var/log/fluentpro/staging.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('ERROR_LOG_FILE_PATH', default='/var/log/fluentpro/staging_error.log'),
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'domains': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'infrastructure': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'application': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Cache configuration for staging
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'fluentpro_staging',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Email configuration for staging
EMAIL_BACKEND = config(
    'EMAIL_BACKEND', 
    default='django.core.mail.backends.console.EmailBackend'  # Console for testing
)

# Monitoring and performance settings
PERFORMANCE_MONITORING_ENABLED = config('PERFORMANCE_MONITORING_ENABLED', default=True, cast=bool)

# Feature flags for staging (similar to production but may enable debug features)
FEATURE_FLAGS = {
    'ENABLE_AI_COMPLETION': config('ENABLE_AI_COMPLETION', default=True, cast=bool),
    'ENABLE_WEBSOCKETS': config('ENABLE_WEBSOCKETS', default=True, cast=bool),
    'ENABLE_BACKGROUND_TASKS': config('ENABLE_BACKGROUND_TASKS', default=True, cast=bool),
    'ENABLE_METRICS_COLLECTION': config('ENABLE_METRICS_COLLECTION', default=True, cast=bool),
    'ENABLE_DISTRIBUTED_TRACING': config('ENABLE_DISTRIBUTED_TRACING', default=True, cast=bool),
    'ENABLE_DEBUG_TOOLBAR': config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool),
}

# API settings for staging
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '10000/hour'
    }
})

# Celery configuration for staging
CELERY_TASK_ROUTES = {
    'domains.authentication.tasks.*': {'queue': 'authentication'},
    'domains.onboarding.tasks.*': {'queue': 'onboarding'},
    'infrastructure.monitoring.*': {'queue': 'monitoring'},
}

# Security middleware for staging
MIDDLEWARE.insert(1, 'django.middleware.security.SecurityMiddleware')

# Session configuration
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=3600*24*7, cast=int)  # 1 week
SESSION_SAVE_EVERY_REQUEST = config('SESSION_SAVE_EVERY_REQUEST', default=False, cast=bool)

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB