"""
Django system checks for FluentPro backend.
Validates configuration and dependencies during startup.
"""

from django.conf import settings
from django.core.checks import register, Error, Warning, Info, Critical
from django.core.checks import Tags
from decouple import config
import os
import sys
from urllib.parse import urlparse


@register(Tags.compatibility)
def check_python_version(app_configs, **kwargs):
    """Check Python version compatibility."""
    errors = []
    
    python_version = sys.version_info
    min_version = (3, 9)
    recommended_version = (3, 11)
    
    if python_version < min_version:
        errors.append(
            Critical(
                f'Python {".".join(map(str, min_version))}+ is required. '
                f'Current version: {".".join(map(str, python_version[:2]))}',
                id='fluentpro.C001',
            )
        )
    elif python_version < recommended_version:
        errors.append(
            Warning(
                f'Python {".".join(map(str, recommended_version))}+ is recommended. '
                f'Current version: {".".join(map(str, python_version[:2]))}',
                id='fluentpro.W001',
            )
        )
    
    return errors


@register(Tags.security)
def check_secret_key(app_configs, **kwargs):
    """Check Django SECRET_KEY configuration."""
    errors = []
    
    secret_key = getattr(settings, 'SECRET_KEY', '')
    
    if not secret_key:
        errors.append(
            Critical(
                'SECRET_KEY setting is empty',
                id='fluentpro.C002',
            )
        )
    elif len(secret_key) < 50:
        errors.append(
            Warning(
                'SECRET_KEY should be at least 50 characters long',
                id='fluentpro.W002',
            )
        )
    elif secret_key == 'django-insecure-!p@9)x$#^tpoh9c9@a82=h7n^g-ifo%joxua3w39=56v%7ne*m':
        errors.append(
            Error(
                'SECRET_KEY is using the default insecure value',
                hint='Set a unique SECRET_KEY in your environment variables',
                id='fluentpro.E001',
            )
        )
    
    return errors


@register(Tags.security)
def check_debug_setting(app_configs, **kwargs):
    """Check DEBUG setting for production."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    debug = getattr(settings, 'DEBUG', True)
    
    if environment == 'production' and debug:
        errors.append(
            Critical(
                'DEBUG must be False in production',
                hint='Set DEBUG=False in your production environment',
                id='fluentpro.C003',
            )
        )
    elif environment == 'staging' and debug:
        errors.append(
            Warning(
                'DEBUG should typically be False in staging',
                id='fluentpro.W003',
            )
        )
    
    return errors


@register(Tags.security)
def check_allowed_hosts(app_configs, **kwargs):
    """Check ALLOWED_HOSTS configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    
    if environment in ['production', 'staging']:
        if not allowed_hosts or allowed_hosts == ['*']:
            errors.append(
                Error(
                    'ALLOWED_HOSTS must be properly configured for production/staging',
                    hint='Set specific hostnames in ALLOWED_HOSTS environment variable',
                    id='fluentpro.E002',
                )
            )
        elif 'localhost' in allowed_hosts or '127.0.0.1' in allowed_hosts:
            errors.append(
                Warning(
                    'ALLOWED_HOSTS contains localhost/127.0.0.1 in production/staging',
                    id='fluentpro.W004',
                )
            )
    
    return errors


@register(Tags.database)
def check_database_configuration(app_configs, **kwargs):
    """Check database configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    databases = getattr(settings, 'DATABASES', {})
    
    if not databases:
        errors.append(
            Critical(
                'No database configuration found',
                id='fluentpro.C004',
            )
        )
        return errors
    
    default_db = databases.get('default', {})
    engine = default_db.get('ENGINE', '')
    
    # Check for production database requirements
    if environment in ['production', 'staging']:
        if 'sqlite3' in engine:
            errors.append(
                Error(
                    f'SQLite is not suitable for {environment} environment',
                    hint='Use PostgreSQL for production/staging',
                    id='fluentpro.E003',
                )
            )
        elif 'postgresql' in engine:
            required_fields = ['NAME', 'USER', 'PASSWORD', 'HOST']
            for field in required_fields:
                if not default_db.get(field):
                    errors.append(
                        Error(
                            f'Database {field} is not configured',
                            hint=f'Set DB_{field} environment variable',
                            id=f'fluentpro.E004',
                        )
                    )
    
    return errors


@register(Tags.caches)
def check_cache_configuration(app_configs, **kwargs):
    """Check cache configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    caches = getattr(settings, 'CACHES', {})
    
    if not caches.get('default'):
        errors.append(
            Warning(
                'No default cache configuration found',
                id='fluentpro.W005',
            )
        )
        return errors
    
    default_cache = caches['default']
    backend = default_cache.get('BACKEND', '')
    
    if environment in ['production', 'staging']:
        if 'locmem' in backend:
            errors.append(
                Warning(
                    f'Local memory cache is not suitable for {environment}',
                    hint='Use Redis cache for production/staging',
                    id='fluentpro.W006',
                )
            )
        elif 'redis' in backend:
            location = default_cache.get('LOCATION', '')
            if not location:
                errors.append(
                    Error(
                        'Redis cache location is not configured',
                        hint='Set REDIS_URL environment variable',
                        id='fluentpro.E005',
                    )
                )
    
    return errors


@register(Tags.compatibility)
def check_external_services(app_configs, **kwargs):
    """Check external service configurations."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    
    # Skip checks for test environment
    if environment == 'testing':
        return errors
    
    # Check Auth0 configuration
    auth0_settings = ['AUTH0_DOMAIN', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET']
    for setting in auth0_settings:
        if not getattr(settings, setting, ''):
            errors.append(
                Error(
                    f'{setting} is not configured',
                    hint=f'Set {setting} environment variable',
                    id='fluentpro.E006',
                )
            )
    
    # Check Supabase configuration
    supabase_settings = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY']
    for setting in supabase_settings:
        value = getattr(settings, setting, '')
        if not value:
            errors.append(
                Error(
                    f'{setting} is not configured',
                    hint=f'Set {setting} environment variable',
                    id='fluentpro.E007',
                )
            )
        elif setting == 'SUPABASE_URL':
            try:
                parsed = urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    errors.append(
                        Error(
                            f'{setting} is not a valid URL',
                            id='fluentpro.E008',
                        )
                    )
            except Exception:
                errors.append(
                    Error(
                        f'{setting} is not a valid URL',
                        id='fluentpro.E008',
                    )
                )
    
    # Check OpenAI configuration
    if not getattr(settings, 'OPENAI_API_KEY', ''):
        errors.append(
            Error(
                'OPENAI_API_KEY is not configured',
                hint='Set OPENAI_API_KEY environment variable',
                id='fluentpro.E009',
            )
        )
    
    return errors


@register(Tags.compatibility)
def check_celery_configuration(app_configs, **kwargs):
    """Check Celery configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    
    broker_url = getattr(settings, 'CELERY_BROKER_URL', '')
    result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', '')
    
    if not broker_url:
        errors.append(
            Warning(
                'CELERY_BROKER_URL is not configured',
                hint='Background tasks will not work without Celery broker',
                id='fluentpro.W007',
            )
        )
    
    if not result_backend:
        errors.append(
            Warning(
                'CELERY_RESULT_BACKEND is not configured',
                hint='Task results will not be stored',
                id='fluentpro.W008',
            )
        )
    
    # Check if Redis is used for both broker and backend
    if broker_url and result_backend:
        if 'redis' in broker_url and 'redis' in result_backend:
            if broker_url == result_backend:
                errors.append(
                    Info(
                        'Using same Redis instance for Celery broker and result backend',
                        hint='Consider using different Redis databases for better isolation',
                        id='fluentpro.I001',
                    )
                )
    
    return errors


@register(Tags.security)
def check_cors_configuration(app_configs, **kwargs):
    """Check CORS configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    
    cors_allow_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
    cors_allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    
    if environment in ['production', 'staging']:
        if cors_allow_all:
            errors.append(
                Error(
                    'CORS_ALLOW_ALL_ORIGINS must be False in production/staging',
                    hint='Configure specific origins in CORS_ALLOWED_ORIGINS',
                    id='fluentpro.E010',
                )
            )
        elif not cors_allowed_origins:
            errors.append(
                Warning(
                    'No CORS allowed origins configured',
                    hint='Configure CORS_ALLOWED_ORIGINS for your frontend',
                    id='fluentpro.W009',
                )
            )
    
    return errors


@register(Tags.compatibility)
def check_logging_configuration(app_configs, **kwargs):
    """Check logging configuration."""
    errors = []
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    logging_config = getattr(settings, 'LOGGING', {})
    
    if not logging_config:
        errors.append(
            Warning(
                'No logging configuration found',
                id='fluentpro.W010',
            )
        )
        return errors
    
    handlers = logging_config.get('handlers', {})
    
    if environment in ['production', 'staging']:
        # Check for file handlers in production
        has_file_handler = any(
            'FileHandler' in handler.get('class', '') 
            for handler in handlers.values()
        )
        
        if not has_file_handler:
            errors.append(
                Warning(
                    'No file logging handler configured for production',
                    hint='Configure file logging for production environments',
                    id='fluentpro.W011',
                )
            )
    
    return errors


@register(Tags.compatibility)
def check_required_packages(app_configs, **kwargs):
    """Check if required packages are installed."""
    errors = []
    
    required_packages = [
        ('redis', 'Redis client for caching and Celery'),
        ('celery', 'Background task processing'),
        ('channels', 'WebSocket support'),
        ('channels_redis', 'Redis channel layer for WebSockets'),
        ('psycopg2', 'PostgreSQL adapter (production)'),
    ]
    
    environment = config('DJANGO_SETTINGS_MODULE', default='').split('.')[-1]
    
    for package, description in required_packages:
        try:
            __import__(package)
        except ImportError:
            if package == 'psycopg2' and environment not in ['production', 'staging']:
                continue  # Skip PostgreSQL check for development
            
            errors.append(
                Warning(
                    f'Required package "{package}" is not installed',
                    hint=f'{description}. Install with: pip install {package}',
                    id='fluentpro.W012',
                )
            )
    
    return errors