"""
Environment variable validation utilities for settings.
Ensures all required configuration is present and properly formatted.
"""

import os
import sys
from typing import Dict, List, Optional, Any, Callable
from decouple import config, UndefinedValueError
from urllib.parse import urlparse


class SettingsValidationError(Exception):
    """Raised when settings validation fails."""
    pass


class EnvironmentValidator:
    """Validates environment variables and settings configuration."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or config('DJANGO_SETTINGS_MODULE', default='config.settings.development').split('.')[-1]
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_required_var(self, var_name: str, var_type: type = str, 
                             description: str = None) -> Any:
        """Validate that a required environment variable is set and properly typed."""
        try:
            value = config(var_name)
            if var_type == bool:
                value = config(var_name, cast=bool)
            elif var_type == int:
                value = config(var_name, cast=int)
            elif var_type == float:
                value = config(var_name, cast=float)
            
            if not value and var_type == str:
                raise SettingsValidationError(f"Environment variable {var_name} is empty")
                
            return value
        except UndefinedValueError:
            error_msg = f"Required environment variable '{var_name}' is not set"
            if description:
                error_msg += f". {description}"
            self.errors.append(error_msg)
            return None
        except (ValueError, TypeError) as e:
            error_msg = f"Environment variable '{var_name}' has invalid type: {str(e)}"
            self.errors.append(error_msg)
            return None
    
    def validate_optional_var(self, var_name: str, default: Any = None, 
                             var_type: type = str, description: str = None) -> Any:
        """Validate an optional environment variable with fallback to default."""
        try:
            if var_type == bool:
                return config(var_name, default=default, cast=bool)
            elif var_type == int:
                return config(var_name, default=default, cast=int)
            elif var_type == float:
                return config(var_name, default=default, cast=float)
            else:
                return config(var_name, default=default)
        except (ValueError, TypeError) as e:
            warning_msg = f"Environment variable '{var_name}' has invalid type, using default: {default}"
            if description:
                warning_msg += f". {description}"
            self.warnings.append(warning_msg)
            return default
    
    def validate_url(self, var_name: str, required: bool = True, 
                    allowed_schemes: List[str] = None) -> Optional[str]:
        """Validate URL format for environment variables."""
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
            
        try:
            url = config(var_name) if required else config(var_name, default=None)
            if not url:
                if required:
                    self.errors.append(f"Required URL environment variable '{var_name}' is not set")
                return None
                
            parsed = urlparse(url)
            if not parsed.scheme:
                self.errors.append(f"URL '{var_name}' missing scheme")
            elif parsed.scheme not in allowed_schemes:
                self.errors.append(f"URL '{var_name}' has invalid scheme '{parsed.scheme}'. Allowed: {allowed_schemes}")
            elif not parsed.netloc:
                self.errors.append(f"URL '{var_name}' missing netloc")
                
            return url
        except UndefinedValueError:
            if required:
                self.errors.append(f"Required URL environment variable '{var_name}' is not set")
            return None
    
    def validate_database_config(self) -> Dict[str, Any]:
        """Validate database configuration for production/staging environments."""
        if self.environment in ['production', 'staging']:
            db_config = {
                'NAME': self.validate_required_var('DB_NAME', description="Database name"),
                'USER': self.validate_required_var('DB_USER', description="Database user"),
                'PASSWORD': self.validate_required_var('DB_PASSWORD', description="Database password"),
                'HOST': self.validate_required_var('DB_HOST', description="Database host"),
                'PORT': self.validate_optional_var('DB_PORT', default='5432', description="Database port"),
            }
            
            # Validate port is numeric
            try:
                port = int(db_config['PORT'])
                if not (1 <= port <= 65535):
                    self.errors.append(f"Database port must be between 1 and 65535, got {port}")
            except (ValueError, TypeError):
                self.errors.append(f"Database port must be numeric, got {db_config['PORT']}")
                
            return db_config
        return {}
    
    def validate_redis_config(self) -> Optional[str]:
        """Validate Redis configuration."""
        redis_url = self.validate_url('REDIS_URL', required=False, allowed_schemes=['redis', 'rediss'])
        
        if redis_url and self.environment in ['production', 'staging']:
            parsed = urlparse(redis_url)
            if not parsed.hostname:
                self.errors.append("Redis URL missing hostname")
            
            # Validate Redis connection (optional check)
            try:
                import redis
                client = redis.from_url(redis_url)
                client.ping()
            except ImportError:
                self.warnings.append("Redis package not installed, cannot validate connection")
            except Exception as e:
                self.warnings.append(f"Could not connect to Redis: {str(e)}")
                
        return redis_url
    
    def validate_external_services(self) -> Dict[str, Any]:
        """Validate external service configurations."""
        services = {}
        
        # Auth0 configuration
        if self.environment != 'testing':
            services['auth0'] = {
                'domain': self.validate_required_var('AUTH0_DOMAIN', description="Auth0 domain"),
                'client_id': self.validate_required_var('AUTH0_CLIENT_ID', description="Auth0 client ID"),
                'client_secret': self.validate_required_var('AUTH0_CLIENT_SECRET', description="Auth0 client secret"),
                'audience': self.validate_optional_var('AUTH0_AUDIENCE', default='https://api.fluentpro.com'),
            }
        
        # Supabase configuration  
        services['supabase'] = {
            'url': self.validate_url('SUPABASE_URL', required=True),
            'anon_key': self.validate_required_var('SUPABASE_ANON_KEY', description="Supabase anonymous key"),
            'service_key': self.validate_required_var('SUPABASE_SERVICE_KEY', description="Supabase service key"),
        }
        
        # OpenAI configuration
        services['openai'] = {
            'api_key': self.validate_required_var('OPENAI_API_KEY', description="OpenAI API key"),
        }
        
        # Azure configuration (optional)
        azure_endpoint = self.validate_url('AZURE_SEARCH_ENDPOINT', required=False)
        if azure_endpoint:
            services['azure'] = {
                'search_endpoint': azure_endpoint,
                'search_key': self.validate_required_var('AZURE_SEARCH_KEY', description="Azure Search key"),
                'openai_endpoint': self.validate_url('AZURE_OPENAI_ENDPOINT', required=False),
                'openai_key': self.validate_optional_var('AZURE_OPENAI_API_KEY'),
            }
        
        return services
    
    def validate_security_settings(self) -> Dict[str, Any]:
        """Validate security-related settings."""
        security = {}
        
        # Secret key validation
        secret_key = self.validate_required_var('SECRET_KEY', description="Django secret key")
        if secret_key:
            if len(secret_key) < 50:
                self.warnings.append("SECRET_KEY should be at least 50 characters long")
            if secret_key == 'django-insecure-!p@9)x$#^tpoh9c9@a82=h7n^g-ifo%joxua3w39=56v%7ne*m':
                self.errors.append("SECRET_KEY is using default insecure value")
        
        # SSL settings for production
        if self.environment == 'production':
            security['ssl_redirect'] = self.validate_optional_var('SECURE_SSL_REDIRECT', default=True, var_type=bool)
            security['session_cookie_secure'] = self.validate_optional_var('SESSION_COOKIE_SECURE', default=True, var_type=bool)
            security['csrf_cookie_secure'] = self.validate_optional_var('CSRF_COOKIE_SECURE', default=True, var_type=bool)
            
            if not security['ssl_redirect']:
                self.warnings.append("SSL redirect is disabled in production")
        
        return security
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validations and return results."""
        results = {
            'environment': self.environment,
            'database': self.validate_database_config(),
            'redis': self.validate_redis_config(),
            'external_services': self.validate_external_services(),
            'security': self.validate_security_settings(),
            'errors': self.errors,
            'warnings': self.warnings,
        }
        
        # Additional environment-specific validations
        if self.environment == 'production':
            debug = self.validate_optional_var('DEBUG', default=False, var_type=bool)
            if debug:
                self.errors.append("DEBUG must be False in production")
        
        return results
    
    def fail_fast_if_errors(self):
        """Raise exception if there are validation errors."""
        if self.errors:
            error_msg = "Settings validation failed:\n" + "\n".join(f"  - {error}" for error in self.errors)
            if self.warnings:
                error_msg += "\n\nWarnings:\n" + "\n".join(f"  - {warning}" for warning in self.warnings)
            raise SettingsValidationError(error_msg)


def validate_environment_settings(environment: str = None) -> Dict[str, Any]:
    """Convenience function to validate current environment settings."""
    validator = EnvironmentValidator(environment)
    results = validator.validate_all()
    
    # Print warnings if any
    if results['warnings']:
        print("⚠️  Settings warnings:")
        for warning in results['warnings']:
            print(f"   {warning}")
    
    # Fail fast on errors in production environments
    if environment in ['production', 'staging']:
        validator.fail_fast_if_errors()
    elif results['errors']:
        print("❌ Settings errors (not failing in development):")
        for error in results['errors']:
            print(f"   {error}")
    
    return results


# Auto-validate on import (can be disabled with SKIP_SETTINGS_VALIDATION=True)
if not config('SKIP_SETTINGS_VALIDATION', default=False, cast=bool):
    try:
        validate_environment_settings()
    except SettingsValidationError as e:
        print(f"❌ {str(e)}")
        if config('DJANGO_SETTINGS_MODULE', default='').endswith('production'):
            sys.exit(1)