"""
Decorators for common functionality across the FluentPro Backend application.
"""

from functools import wraps
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import json
import logging

from authentication.backends import Auth0JWTAuthentication
from .responses import APIResponse
from .exceptions import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


def fluentpro_api_view(http_methods=None, authenticated=True):
    """
    Decorator that combines common DRF decorators for FluentPro API views.
    
    Args:
        http_methods: List of HTTP methods (default: ['POST'])
        authenticated: Whether authentication is required (default: True)
    
    Returns:
        Decorated function with standard FluentPro API setup
    """
    if http_methods is None:
        http_methods = ['POST']
    
    def decorator(func):
        # Apply DRF decorators
        func = api_view(http_methods)(func)
        
        if authenticated:
            func = authentication_classes([Auth0JWTAuthentication])(func)
            func = permission_classes([IsAuthenticated])(func)
        
        return func
    
    return decorator


def handle_exceptions(func):
    """
    Decorator that provides consistent exception handling for view functions.
    
    Args:
        func: The view function to wrap
        
    Returns:
        Decorated function with exception handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from .exceptions import FluentProException
            
            if isinstance(e, FluentProException):
                return APIResponse.error(
                    message=e.message,
                    details=e.details if e.details else None,
                    status_code=getattr(e, 'status_code', 400),
                    error_code=e.error_code
                )
            
            # Log unexpected exceptions
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            
            return APIResponse.internal_error(
                message="An unexpected error occurred",
                log_message=str(e)
            )
    
    return wrapper


def validate_json_payload(*required_fields):
    """
    Decorator that validates JSON payload and extracts required fields.
    
    Args:
        *required_fields: Field names that are required in the JSON payload
        
    Returns:
        Decorated function that validates JSON and injects validated data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                # Parse JSON
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return APIResponse.validation_error({
                        "json": ["Invalid JSON payload"]
                    })
                
                # Validate required fields
                missing_fields = []
                for field in required_fields:
                    if field not in data or not data[field]:
                        missing_fields.append(field)
                
                if missing_fields:
                    errors = {field: ["This field is required"] for field in missing_fields}
                    return APIResponse.validation_error(errors)
                
                # Inject validated data into kwargs
                kwargs['validated_data'] = data
                
                return func(request, *args, **kwargs)
                
            except Exception as e:
                logger.exception(f"Error in validate_json_payload for {func.__name__}: {str(e)}")
                return APIResponse.internal_error()
        
        return wrapper
    return decorator


def require_auth0_user(func):
    """
    Decorator that ensures the user has a valid Auth0 ID.
    
    Args:
        func: The view function to wrap
        
    Returns:
        Decorated function that validates Auth0 user
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            auth0_id = getattr(request.user, 'sub', None)
            if not auth0_id:
                return APIResponse.unauthorized("Invalid authentication: Auth0 ID not found")
            
            # Inject auth0_id into kwargs for convenience
            kwargs['auth0_id'] = auth0_id
            
            return func(request, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in require_auth0_user for {func.__name__}: {str(e)}")
            return APIResponse.internal_error()
    
    return wrapper


def require_supabase_user(func):
    """
    Decorator that ensures the user exists in Supabase.
    
    Args:
        func: The view function to wrap
        
    Returns:
        Decorated function that validates Supabase user exists
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            from authentication.services.supabase_service import SupabaseService
            
            auth0_id = getattr(request.user, 'sub', None)
            if not auth0_id:
                return APIResponse.unauthorized("Invalid authentication: Auth0 ID not found")
            
            supabase_service = SupabaseService()
            user = supabase_service.get_user_by_auth0_id(auth0_id)
            
            if not user:
                return APIResponse.not_found("User not found in our system")
            
            # Inject user data into kwargs
            kwargs['auth0_id'] = auth0_id
            kwargs['user_data'] = user
            
            return func(request, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in require_supabase_user for {func.__name__}: {str(e)}")
            return APIResponse.internal_error()
    
    return wrapper


def log_api_call(func):
    """
    Decorator that logs API calls for debugging and monitoring.
    
    Args:
        func: The view function to wrap
        
    Returns:
        Decorated function with logging
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Log request
        auth0_id = getattr(request.user, 'sub', 'anonymous') if hasattr(request, 'user') else 'anonymous'
        logger.info(f"API call: {func.__name__} by user {auth0_id}")
        
        try:
            response = func(request, *args, **kwargs)
            
            # Log response status
            status_code = getattr(response, 'status_code', 'unknown')
            logger.info(f"API response: {func.__name__} returned {status_code}")
            
            return response
            
        except Exception as e:
            logger.error(f"API error: {func.__name__} failed with {str(e)}")
            raise
    
    return wrapper


def validate_industry_selection(func):
    """
    Decorator that validates user has selected an industry before allowing access.
    
    Args:
        func: The view function to wrap
        
    Returns:
        Decorated function that validates industry selection
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            from authentication.services.supabase_service import SupabaseService
            
            auth0_id = getattr(request.user, 'sub', None)
            if not auth0_id:
                return APIResponse.unauthorized("Invalid authentication")
            
            supabase_service = SupabaseService()
            user_profile = supabase_service.get_user_full_profile(auth0_id)
            
            if not user_profile:
                return APIResponse.not_found("User not found")
            
            if not user_profile.get('industry_id'):
                return APIResponse.error(
                    message="Industry selection required",
                    error_code="INDUSTRY_NOT_SELECTED",
                    status_code=status.HTTP_428_PRECONDITION_REQUIRED
                )
            
            # Inject user profile for convenience
            kwargs['user_profile'] = user_profile
            
            return func(request, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in validate_industry_selection for {func.__name__}: {str(e)}")
            return APIResponse.internal_error()
    
    return wrapper


def validate_onboarding_phase(required_phase):
    """
    Decorator that validates user has completed a specific onboarding phase.
    
    Args:
        required_phase: The onboarding phase that must be completed
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                from authentication.services.supabase_service import SupabaseService
                
                auth0_id = getattr(request.user, 'sub', None)
                if not auth0_id:
                    return APIResponse.unauthorized("Invalid authentication")
                
                supabase_service = SupabaseService()
                user_profile = supabase_service.get_user_full_profile(auth0_id)
                
                if not user_profile:
                    return APIResponse.not_found("User not found")
                
                current_phase = user_profile.get('onboarding_status', 'not_started')
                
                # Define phase order for validation
                phase_order = ['not_started', 'basic_info', 'industry_selected', 'role_selected', 'communication_needs', 'completed']
                
                if required_phase not in phase_order:
                    logger.error(f"Invalid required phase: {required_phase}")
                    return APIResponse.internal_error("Invalid onboarding phase configuration")
                
                required_index = phase_order.index(required_phase)
                current_index = phase_order.index(current_phase) if current_phase in phase_order else 0
                
                if current_index < required_index:
                    return APIResponse.error(
                        message=f"Onboarding phase '{required_phase}' must be completed",
                        error_code="ONBOARDING_INCOMPLETE",
                        status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                        details={
                            "required_phase": required_phase,
                            "current_phase": current_phase
                        }
                    )
                
                # Inject user profile for convenience
                kwargs['user_profile'] = user_profile
                
                return func(request, *args, **kwargs)
                
            except Exception as e:
                logger.exception(f"Error in validate_onboarding_phase for {func.__name__}: {str(e)}")
                return APIResponse.internal_error()
        
        return wrapper
    return decorator