"""
Authentication and authorization event logging middleware.

Provides comprehensive logging of authentication and authorization events
including login attempts, permission checks, and security-related activities.
"""

import threading
from typing import Callable

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.dispatch import receiver

from infrastructure.monitoring.logging_config import get_logger


class AuthEventLoggingMiddleware:
    """
    Middleware that logs authentication and authorization events.
    
    This middleware:
    1. Tracks user authentication status changes
    2. Logs permission denied events
    3. Adds authentication context to thread-local storage
    4. Provides structured logging for security auditing
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """Initialize the middleware with the next middleware/view in the chain."""
        self.get_response = get_response
        self.logger = get_logger(__name__)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request with authentication logging."""
        
        # Store request context in thread-local storage for logging access
        self._store_request_context(request)
        
        # Track authentication status before request processing
        was_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        user_before = getattr(request, 'user', None)
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # Check for authentication status changes
            is_authenticated = hasattr(request, 'user') and request.user.is_authenticated
            user_after = getattr(request, 'user', None)
            
            # Log authentication status changes
            if not was_authenticated and is_authenticated:
                self.logger.info(
                    "User authenticated during request",
                    event_type="auth_status_change",
                    user_id=getattr(user_after, 'id', None),
                    user_email=getattr(user_after, 'email', None),
                    path=request.path,
                    method=request.method,
                )
            elif was_authenticated and not is_authenticated:
                self.logger.info(
                    "User deauthenticated during request",
                    event_type="auth_status_change",
                    user_id=getattr(user_before, 'id', None),
                    user_email=getattr(user_before, 'email', None),
                    path=request.path,
                    method=request.method,
                )
            
            return response
            
        except PermissionDenied as exc:
            # Log permission denied events
            self.logger.warning(
                "Permission denied",
                event_type="authorization_denied",
                user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                user_email=getattr(request.user, 'email', None) if hasattr(request, 'user') else None,
                path=request.path,
                method=request.method,
                exception_message=str(exc),
                is_authenticated=hasattr(request, 'user') and request.user.is_authenticated,
            )
            raise
            
        except Exception as exc:
            # Log other authentication-related errors
            if 'auth' in str(exc).lower() or 'permission' in str(exc).lower():
                self.logger.error(
                    "Authentication/Authorization error",
                    event_type="auth_error",
                    user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                    user_email=getattr(request.user, 'email', None) if hasattr(request, 'user') else None,
                    path=request.path,
                    method=request.method,
                    exception_type=type(exc).__name__,
                    exception_message=str(exc),
                )
            raise
            
        finally:
            # Clean up thread-local storage
            self._cleanup_request_context()

    def _store_request_context(self, request: HttpRequest) -> None:
        """Store request context in thread-local storage for logging processors."""
        request_context = {
            'method': request.method,
            'path': request.path,
            'remote_addr': self._get_client_ip(request),
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            request_context.update({
                'user_id': getattr(request.user, 'id', None),
                'user_email': getattr(request.user, 'email', None),
                'is_authenticated': True,
            })
        else:
            request_context['is_authenticated'] = False
        
        threading.current_thread().request_context = request_context

    def _cleanup_request_context(self) -> None:
        """Clean up thread-local storage to prevent memory leaks."""
        if hasattr(threading.current_thread(), 'request_context'):
            delattr(threading.current_thread(), 'request_context')

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


# Signal handlers for Django authentication events
logger = get_logger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login events."""
    logger.info(
        "User logged in successfully",
        event_type="user_login_success",
        user_id=getattr(user, 'id', None),
        user_email=getattr(user, 'email', None),
        username=getattr(user, 'username', None),
        remote_addr=_get_client_ip_from_request(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events."""
    logger.info(
        "User logged out",
        event_type="user_logout",
        user_id=getattr(user, 'id', None),
        user_email=getattr(user, 'email', None),
        username=getattr(user, 'username', None),
        remote_addr=_get_client_ip_from_request(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    logger.warning(
        "User login failed",
        event_type="user_login_failed",
        username=credentials.get('username', 'unknown'),
        remote_addr=_get_client_ip_from_request(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
    )


def _get_client_ip_from_request(request) -> str:
    """Extract client IP address from request headers."""
    if not request:
        return 'unknown'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip