"""
Test-specific Django settings.
Optimized for fast test execution with minimal external dependencies.
"""

from .base import *
import tempfile
import os

# Test mode flag
TESTING = True
DEBUG = True

# Database configuration for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 10,
        },
        'TEST': {
            'NAME': ':memory:',
        }
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Cache configuration for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Static files configuration for testing
STATIC_URL = '/static/'
STATIC_ROOT = tempfile.mkdtemp()

MEDIA_URL = '/media/'
MEDIA_ROOT = tempfile.mkdtemp()

# Logging configuration for testing
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',  # Only show errors during tests
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'domains': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'infrastructure': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'application': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'ERROR',
    },
}

# Password validation (simplified for testing)
AUTH_PASSWORD_VALIDATORS = []

# Internationalization (simplified for testing)
USE_TZ = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'

# Celery configuration for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Redis configuration for testing (using fake redis)
REDIS_URL = 'redis://localhost:6379/15'  # Use different DB for tests

# External service configurations (mocked in tests)
OPENAI_API_KEY = 'test-openai-key'
OPENAI_ORGANIZATION = 'test-org'

AUTH0_DOMAIN = 'test.auth0.com'
AUTH0_CLIENT_ID = 'test-client-id'
AUTH0_CLIENT_SECRET = 'test-client-secret'
AUTH0_AUDIENCE = 'test-audience'

AZURE_SEARCH_SERVICE_NAME = 'test-search'
AZURE_SEARCH_API_KEY = 'test-api-key'
AZURE_SEARCH_INDEX_NAME = 'test-index'

# Supabase configuration for testing
SUPABASE_URL = 'https://test.supabase.co'
SUPABASE_ANON_KEY = 'test-anon-key'
SUPABASE_SERVICE_ROLE_KEY = 'test-service-key'

# Security settings for testing
SECRET_KEY = 'test-secret-key-not-for-production-use-only-in-tests'
ALLOWED_HOSTS = ['*']

# CORS settings for testing
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Session configuration for testing
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour for tests

# Channel layers for WebSocket testing
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# File upload settings for testing
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB

# Test-specific middleware (remove some for speed)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Skip some middleware for faster tests
]

# Disable some features for testing
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# Test database settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# API testing settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Permissive for tests
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_PAGINATION_CLASS': None,  # Disable pagination in tests
}

# Spectacular settings for API documentation testing
SPECTACULAR_SETTINGS = {
    'TITLE': 'FluentPro API (Test)',
    'DESCRIPTION': 'Test API documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Don't include schema in tests
}

# Performance monitoring (disabled for tests)
PERFORMANCE_MONITORING_ENABLED = False

# Feature flags for testing
FEATURE_FLAGS = {
    'ENABLE_AI_COMPLETION': True,
    'ENABLE_WEBSOCKETS': True,
    'ENABLE_BACKGROUND_TASKS': False,  # Disable for faster tests
    'ENABLE_METRICS_COLLECTION': False,
    'ENABLE_DISTRIBUTED_TRACING': False,
}

# Test data configuration
TEST_DATA_CONFIG = {
    'CREATE_SAMPLE_DATA': False,
    'USE_FIXTURES': True,
    'RESET_BETWEEN_TESTS': True,
}

# Mock service configuration
MOCK_EXTERNAL_SERVICES = True
MOCK_AI_SERVICES = True
MOCK_AUTH_SERVICES = True

# Testing utilities
TEST_UTILS = {
    'ASSERT_NUM_QUERIES': True,
    'ASSERT_MAX_QUERIES': 10,
    'ASSERT_PERFORMANCE': True,
    'MAX_RESPONSE_TIME': 1.0,  # seconds
}

# Async configuration for testing
ASGI_APPLICATION = 'config.asgi.application'

# WebSocket testing configuration
WEBSOCKET_ACCEPT_ALL = True

# Search configuration for testing
SEARCH_BACKEND = 'test'  # Use test search backend

# AI service configuration for testing
AI_SERVICE_CONFIG = {
    'PROVIDER': 'mock',
    'MOCK_RESPONSES': True,
    'SIMULATE_DELAYS': False,
    'SIMULATE_FAILURES': False,
}

# Monitoring and observability (disabled for tests)
MONITORING_CONFIG = {
    'ENABLE_METRICS': False,
    'ENABLE_TRACING': False,
    'ENABLE_LOGGING': False,
    'ENABLE_HEALTH_CHECKS': False,
}

# Security settings (relaxed for testing)
SECURITY_CONFIG = {
    'ENFORCE_HTTPS': False,
    'VALIDATE_TOKENS': False,  # Use mock validation
    'RATE_LIMITING': False,
    'CSRF_PROTECTION': False,
}

# Cleanup configuration
CLEANUP_CONFIG = {
    'AUTO_CLEANUP': True,
    'CLEANUP_TEMP_FILES': True,
    'CLEANUP_CACHE': True,
    'CLEANUP_SESSIONS': True,
}