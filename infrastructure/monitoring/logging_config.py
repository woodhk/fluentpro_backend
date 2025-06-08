"""
Structured logging configuration using structlog.
Provides JSON-formatted logs with timestamps and context metadata.
"""

import logging
import sys
from typing import Any, Dict, List

import structlog
from structlog.typing import Processor


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID from request context if available."""
    from django.core.exceptions import AppRegistryNotReady
    
    try:
        from django.http import HttpRequest
        from django.utils.deprecation import MiddlewareMixin
        import threading
        
        # Get correlation ID from thread local storage
        correlation_id = getattr(threading.current_thread(), 'correlation_id', None)
        if correlation_id:
            event_dict['correlation_id'] = correlation_id
            
    except (ImportError, AppRegistryNotReady):
        # During Django startup or in contexts without Django
        pass
    
    return event_dict


def add_request_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request context information if available."""
    from django.core.exceptions import AppRegistryNotReady
    
    try:
        import threading
        
        # Get request context from thread local storage
        request_context = getattr(threading.current_thread(), 'request_context', None)
        if request_context:
            event_dict.update({
                'user_id': request_context.get('user_id'),
                'request_method': request_context.get('method'),
                'request_path': request_context.get('path'),
                'remote_addr': request_context.get('remote_addr'),
            })
            
    except (ImportError, AppRegistryNotReady):
        # During Django startup or in contexts without Django
        pass
    
    return event_dict


def add_application_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add application-level context metadata."""
    event_dict.update({
        'service': 'fluentpro_backend',
        'version': '1.0.0',
        'component': event_dict.get('logger', 'unknown'),
    })
    return event_dict


def configure_structlog(
    log_level: str = "INFO",
    development_mode: bool = True,
    json_format: bool = True
) -> None:
    """
    Configure structlog for the application.
    
    Args:
        log_level: Minimum log level to output
        development_mode: Whether to use development-friendly formatting
        json_format: Whether to output JSON format (True) or pretty format (False)
    """
    
    # Define processors pipeline
    processors: List[Processor] = [
        # Filter by log level
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        
        # Add custom context
        add_application_context,
        add_correlation_id,
        add_request_context,
        
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if development_mode and not json_format:
        # Pretty console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    else:
        # JSON output for production and structured logging
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured structlog logger
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return structlog.get_logger(name)


# Export commonly used functions
__all__ = [
    'configure_structlog',
    'get_logger',
    'add_correlation_id',
    'add_request_context',
    'add_application_context',
]