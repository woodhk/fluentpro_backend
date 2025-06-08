"""
Request/Response logging middleware with performance timing.

Provides comprehensive logging of HTTP requests and responses including
timing metrics, user context, and request/response details.
"""

import time
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from infrastructure.monitoring.logging_config import get_logger


class RequestResponseLoggingMiddleware:
    """
    Middleware that logs HTTP requests and responses with performance metrics.
    
    This middleware:
    1. Logs incoming requests with method, path, user info, and headers
    2. Measures request processing time
    3. Logs outgoing responses with status code and timing
    4. Adds structured logging with correlation IDs
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize the middleware with the next middleware/view in the chain."""
        self.get_response = get_response
        self.logger = get_logger(__name__)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request with logging and timing."""
        
        # Record start time for performance measurement
        start_time = time.time()
        
        # Extract request details
        user_id = None
        user_email = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = getattr(request.user, 'id', None)
            user_email = getattr(request.user, 'email', None)
        
        # Log incoming request
        self.logger.info(
            "Incoming request",
            event_type="request_start",
            method=request.method,
            path=request.path,
            query_string=request.META.get('QUERY_STRING', ''),
            user_id=user_id,
            user_email=user_email,
            remote_addr=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            content_type=request.META.get('CONTENT_TYPE', ''),
            content_length=request.META.get('CONTENT_LENGTH', 0),
        )
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Log successful response
            self.logger.info(
                "Request completed",
                event_type="request_complete",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                processing_time_ms=round(processing_time * 1000, 2),
                response_size=len(response.content) if hasattr(response, 'content') else 0,
                user_id=user_id,
                user_email=user_email,
            )
            
            # Log performance warnings for slow requests
            if processing_time > 1.0:  # More than 1 second
                self.logger.warning(
                    "Slow request detected",
                    event_type="performance_warning",
                    method=request.method,
                    path=request.path,
                    processing_time_ms=round(processing_time * 1000, 2),
                    user_id=user_id,
                )
            
            return response
            
        except Exception as exc:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            
            # Log request failure
            self.logger.error(
                "Request failed",
                event_type="request_error",
                method=request.method,
                path=request.path,
                processing_time_ms=round(processing_time * 1000, 2),
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                user_id=user_id,
                user_email=user_email,
            )
            
            # Re-raise the exception
            raise

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip