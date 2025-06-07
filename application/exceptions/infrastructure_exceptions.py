"""
Infrastructure Exceptions

Exception types for infrastructure layer failures.
"""

from typing import Optional, Dict, Any


class InfrastructureException(Exception):
    """
    Base exception for infrastructure layer failures.
    
    This exception wraps lower-level infrastructure errors
    to provide a consistent interface to the domain layer.
    """
    
    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.original_exception = original_exception
        self.context = context or {}


class ExternalServiceException(InfrastructureException):
    """
    Exception for external service failures.
    
    Raised when external APIs (Auth0, OpenAI, etc.) fail.
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        error_code: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, original_exception, context)
        self.service_name = service_name
        self.error_code = error_code


class DatabaseException(InfrastructureException):
    """
    Exception for database operation failures.
    
    Raised when database operations fail.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, original_exception, context)
        self.operation = operation
        self.table = table


class CacheException(InfrastructureException):
    """
    Exception for cache operation failures.
    
    Raised when cache operations fail.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, original_exception, context)
        self.operation = operation
        self.key = key


class AuthenticationServiceException(ExternalServiceException):
    """
    Exception for authentication service failures.
    
    Raised when authentication provider operations fail.
    """
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            service_name="authentication",
            original_exception=original_exception,
            context=context
        )
        self.user_id = user_id
        self.operation = operation


class AIServiceException(ExternalServiceException):
    """
    Exception for AI service failures.
    
    Raised when AI/ML service operations fail.
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            service_name="ai_service",
            original_exception=original_exception,
            context=context
        )
        self.model = model
        self.operation = operation