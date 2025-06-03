"""
Custom exceptions for FluentPro Backend application.
Provides domain-specific exceptions for better error handling and debugging.
"""

from rest_framework import status
from typing import Optional, Dict, Any


class FluentProException(Exception):
    """
    Base exception class for all FluentPro-specific exceptions.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(FluentProException):
    """
    Raised when authentication fails.
    """
    
    def __init__(
        self, 
        message: str = "Authentication failed", 
        error_code: str = "AUTH_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationError(FluentProException):
    """
    Raised when user lacks required permissions.
    """
    
    def __init__(
        self, 
        message: str = "Access denied", 
        error_code: str = "ACCESS_DENIED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_403_FORBIDDEN


class ValidationError(FluentProException):
    """
    Raised when data validation fails.
    """
    
    def __init__(
        self, 
        message: str = "Validation failed", 
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_400_BAD_REQUEST


class ResourceNotFoundError(FluentProException):
    """
    Raised when a requested resource is not found.
    """
    
    def __init__(
        self, 
        resource_type: str = "Resource",
        resource_id: Optional[str] = None,
        error_code: str = "NOT_FOUND"
    ):
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"
        
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_404_NOT_FOUND


class ConflictError(FluentProException):
    """
    Raised when a resource conflict occurs (e.g., duplicate email).
    """
    
    def __init__(
        self, 
        message: str = "Resource conflict", 
        error_code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_409_CONFLICT


class ServiceUnavailableError(FluentProException):
    """
    Raised when an external service is unavailable.
    """
    
    def __init__(
        self, 
        service_name: str,
        message: Optional[str] = None,
        error_code: str = "SERVICE_UNAVAILABLE"
    ):
        if not message:
            message = f"{service_name} service is currently unavailable"
        
        details = {"service_name": service_name}
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ExternalServiceError(FluentProException):
    """
    Raised when an external service returns an error.
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str,
        service_error: Optional[str] = None,
        error_code: str = "EXTERNAL_SERVICE_ERROR"
    ):
        details = {
            "service_name": service_name,
            "service_error": service_error
        }
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_502_BAD_GATEWAY


class BusinessLogicError(FluentProException):
    """
    Raised when business logic constraints are violated.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "BUSINESS_LOGIC_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ConfigurationError(FluentProException):
    """
    Raised when there's a configuration issue.
    """
    
    def __init__(
        self, 
        message: str = "Configuration error", 
        error_code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class DatabaseError(FluentProException):
    """
    Raised when database operations fail.
    """
    
    def __init__(
        self, 
        message: str = "Database operation failed", 
        error_code: str = "DATABASE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# Auth0-specific exceptions
class Auth0Error(ExternalServiceError):
    """
    Raised when Auth0 service returns an error.
    """
    
    def __init__(self, message: str, auth0_error: Optional[str] = None):
        super().__init__(
            service_name="Auth0",
            message=message,
            service_error=auth0_error,
            error_code="AUTH0_ERROR"
        )


class Auth0UserNotFoundError(ResourceNotFoundError):
    """
    Raised when Auth0 user is not found.
    """
    
    def __init__(self, user_identifier: str):
        super().__init__(
            resource_type="Auth0 User",
            resource_id=user_identifier,
            error_code="AUTH0_USER_NOT_FOUND"
        )


# Supabase-specific exceptions
class SupabaseError(ExternalServiceError):
    """
    Raised when Supabase service returns an error.
    """
    
    def __init__(self, message: str, supabase_error: Optional[str] = None):
        super().__init__(
            service_name="Supabase",
            message=message,
            service_error=supabase_error,
            error_code="SUPABASE_ERROR"
        )


class SupabaseUserNotFoundError(ResourceNotFoundError):
    """
    Raised when Supabase user is not found.
    """
    
    def __init__(self, user_identifier: str):
        super().__init__(
            resource_type="User",
            resource_id=user_identifier,
            error_code="USER_NOT_FOUND"
        )


# Azure-specific exceptions
class AzureSearchError(ExternalServiceError):
    """
    Raised when Azure Search service returns an error.
    """
    
    def __init__(self, message: str, azure_error: Optional[str] = None):
        super().__init__(
            service_name="Azure Search",
            message=message,
            service_error=azure_error,
            error_code="AZURE_SEARCH_ERROR"
        )


class AzureOpenAIError(ExternalServiceError):
    """
    Raised when Azure OpenAI service returns an error.
    """
    
    def __init__(self, message: str, azure_error: Optional[str] = None):
        super().__init__(
            service_name="Azure OpenAI",
            message=message,
            service_error=azure_error,
            error_code="AZURE_OPENAI_ERROR"
        )


# Onboarding-specific exceptions
class OnboardingError(BusinessLogicError):
    """
    Raised when onboarding process encounters an error.
    """
    
    def __init__(self, message: str, phase: Optional[str] = None):
        details = {}
        if phase:
            details["onboarding_phase"] = phase
            
        super().__init__(
            message=message,
            error_code="ONBOARDING_ERROR",
            details=details
        )


class IncompleteOnboardingError(BusinessLogicError):
    """
    Raised when user tries to access functionality requiring completed onboarding.
    """
    
    def __init__(self, required_phase: str, current_phase: Optional[str] = None):
        message = f"Onboarding phase '{required_phase}' must be completed to access this functionality"
        details = {
            "required_phase": required_phase,
            "current_phase": current_phase
        }
        
        super().__init__(
            message=message,
            error_code="INCOMPLETE_ONBOARDING",
            details=details
        )