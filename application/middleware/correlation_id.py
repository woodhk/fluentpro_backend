"""
Correlation ID middleware for request tracing.

Generates and injects unique correlation IDs for each request to enable
distributed tracing across the application and external services.
"""

import threading
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse


class CorrelationIdMiddleware:
    """
    Middleware that generates and injects correlation IDs for request tracing.
    
    This middleware:
    1. Generates a unique correlation ID for each request
    2. Stores it in thread-local storage for logging access
    3. Adds it to the request object for view access
    4. Includes it in response headers for client-side tracing
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize the middleware with the next middleware/view in the chain."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and inject correlation ID."""
        
        # Check if correlation ID is already present in headers (from upstream services)
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
        
        if not correlation_id:
            # Generate new correlation ID if not present
            correlation_id = str(uuid.uuid4())
        
        # Store correlation ID in thread-local storage for logging access
        threading.current_thread().correlation_id = correlation_id
        
        # Add correlation ID to request object for view access
        request.correlation_id = correlation_id
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # Add correlation ID to response headers
            response['X-Correlation-ID'] = correlation_id
            
            return response
            
        finally:
            # Clean up thread-local storage to prevent memory leaks
            if hasattr(threading.current_thread(), 'correlation_id'):
                delattr(threading.current_thread(), 'correlation_id')