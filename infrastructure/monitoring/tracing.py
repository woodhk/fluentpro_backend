"""
Distributed tracing infrastructure for request flow tracking.

Provides comprehensive distributed tracing capabilities for tracking requests
across services, external API calls, and internal operations with span management
and trace context propagation.
"""

import functools
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum

from infrastructure.monitoring.logging_config import get_logger
from infrastructure.monitoring.metrics import APP_METRICS


class SpanKind(Enum):
    """Types of spans in distributed tracing."""
    SERVER = "server"           # Incoming request
    CLIENT = "client"           # Outgoing request  
    PRODUCER = "producer"       # Message producer
    CONSUMER = "consumer"       # Message consumer
    INTERNAL = "internal"       # Internal operation


class SpanStatus(Enum):
    """Status of a span."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Context information for a span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1  # Sampled by default
    trace_state: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpanEvent:
    """Event within a span."""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Distributed tracing span."""
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    parent_span: Optional['Span'] = None
    
    def __post_init__(self):
        """Initialize span after creation."""
        self.logger = get_logger(__name__)
    
    def set_attribute(self, key: str, value: Any) -> 'Span':
        """Set an attribute on the span."""
        self.attributes[key] = value
        return self
    
    def set_attributes(self, attributes: Dict[str, Any]) -> 'Span':
        """Set multiple attributes on the span."""
        self.attributes.update(attributes)
        return self
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> 'Span':
        """Add an event to the span."""
        event = SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {}
        )
        self.events.append(event)
        return self
    
    def set_status(self, status: SpanStatus, description: str = "") -> 'Span':
        """Set the span status."""
        self.status = status
        if description:
            self.attributes['status_description'] = description
        return self
    
    def finish(self, end_time: Optional[float] = None) -> None:
        """Mark the span as finished."""
        self.end_time = end_time or time.time()
        
        # Calculate duration
        duration = self.end_time - self.start_time
        
        # Log span completion
        self.logger.info(
            "Span completed",
            span_name=self.name,
            trace_id=self.context.trace_id,
            span_id=self.context.span_id,
            parent_span_id=self.context.parent_span_id,
            kind=self.kind.value,
            status=self.status.value,
            duration_ms=round(duration * 1000, 2),
            attributes=self.attributes,
            event_count=len(self.events)
        )
        
        # Record metrics
        labels = {
            'span_name': self.name,
            'kind': self.kind.value,
            'status': self.status.value
        }
        APP_METRICS['http_request_duration'].observe(duration, labels)
        
        # Remove from current span context
        TracingContext.get_instance().finish_span(self)
    
    def get_duration(self) -> Optional[float]:
        """Get span duration if finished."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_recording(self) -> bool:
        """Check if span is still recording."""
        return self.end_time is None


class TracingContext:
    """Thread-local tracing context manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.local = threading.local()
    
    @classmethod
    def get_instance(cls) -> 'TracingContext':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return getattr(self.local, 'current_span', None)
    
    def set_current_span(self, span: Optional[Span]) -> None:
        """Set the current active span."""
        self.local.current_span = span
    
    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID."""
        current_span = self.get_current_span()
        return current_span.context.trace_id if current_span else None
    
    def start_span(self, span: Span) -> None:
        """Start a new span and set it as current."""
        self.set_current_span(span)
    
    def finish_span(self, span: Span) -> None:
        """Finish a span and restore parent."""
        if self.get_current_span() == span:
            self.set_current_span(span.parent_span)


class Tracer:
    """Distributed tracer for creating and managing spans."""
    
    def __init__(self, service_name: str = "fluentpro_backend"):
        self.service_name = service_name
        self.logger = get_logger(__name__)
        self.context = TracingContext.get_instance()
    
    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
                   parent: Optional[Span] = None,
                   attributes: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span."""
        
        # Get parent span
        if parent is None:
            parent = self.context.get_current_span()
        
        # Create span context
        if parent:
            trace_id = parent.context.trace_id
            parent_span_id = parent.context.span_id
        else:
            trace_id = str(uuid.uuid4())
            parent_span_id = None
        
        span_context = SpanContext(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id
        )
        
        # Create span
        span = Span(
            name=name,
            context=span_context,
            kind=kind,
            parent_span=parent
        )
        
        # Set default attributes
        span.set_attributes({
            'service.name': self.service_name,
            'service.version': '1.0.0',
        })
        
        if attributes:
            span.set_attributes(attributes)
        
        # Start the span
        self.context.start_span(span)
        
        self.logger.debug(
            "Span started",
            span_name=name,
            trace_id=span.context.trace_id,
            span_id=span.context.span_id,
            parent_span_id=parent_span_id,
            kind=kind.value
        )
        
        return span
    
    @contextmanager
    def span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
             attributes: Optional[Dict[str, Any]] = None):
        """Context manager for automatic span lifecycle."""
        span = self.start_span(name, kind, attributes=attributes)
        try:
            yield span
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            span.add_event("exception", {
                'exception.type': type(e).__name__,
                'exception.message': str(e)
            })
            raise
        finally:
            span.finish()
    
    def extract_context_from_headers(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract tracing context from HTTP headers."""
        trace_id = headers.get('x-trace-id')
        parent_span_id = headers.get('x-parent-span-id')
        
        if trace_id:
            return SpanContext(
                trace_id=trace_id,
                span_id=str(uuid.uuid4()),
                parent_span_id=parent_span_id
            )
        return None
    
    def inject_context_to_headers(self, headers: Dict[str, str], 
                                 span: Optional[Span] = None) -> Dict[str, str]:
        """Inject tracing context into HTTP headers."""
        if span is None:
            span = self.context.get_current_span()
        
        if span:
            headers = headers.copy()
            headers['x-trace-id'] = span.context.trace_id
            headers['x-parent-span-id'] = span.context.span_id
            
            # Also add correlation ID for compatibility
            correlation_id = getattr(threading.current_thread(), 'correlation_id', None)
            if correlation_id:
                headers['x-correlation-id'] = correlation_id
        
        return headers


# Global tracer instance
_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    return _tracer


def trace_operation(name: str, kind: SpanKind = SpanKind.INTERNAL,
                   attributes: Optional[Dict[str, Any]] = None):
    """Decorator for automatic operation tracing."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.span(name, kind, attributes) as span:
                # Add function information
                span.set_attributes({
                    'function.name': func.__name__,
                    'function.module': func.__module__,
                })
                
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


def trace_http_client(service_name: str, method: str = "GET", url: str = ""):
    """Decorator for tracing HTTP client calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            attributes = {
                'http.method': method,
                'http.url': url,
                'http.client.name': service_name,
            }
            
            with tracer.span(f"HTTP {method} {service_name}", SpanKind.CLIENT, attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    
                    # Extract response info if available
                    if hasattr(result, 'status_code'):
                        span.set_attribute('http.status_code', result.status_code)
                        if result.status_code >= 400:
                            span.set_status(SpanStatus.ERROR)
                    
                    return result
                except Exception as e:
                    span.set_attribute('http.error', str(e))
                    raise
        return wrapper
    return decorator


def trace_database_operation(operation: str, table: str = ""):
    """Decorator for tracing database operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            attributes = {
                'db.operation': operation,
                'db.table': table,
                'db.system': 'supabase',
            }
            
            with tracer.span(f"DB {operation}", SpanKind.CLIENT, attributes) as span:
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


class TracingMiddleware:
    """Django middleware for HTTP request tracing."""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.tracer = get_tracer()
    
    def __call__(self, request):
        """Process request with distributed tracing."""
        
        # Extract tracing context from headers
        headers = {k.replace('HTTP_', '').lower().replace('_', '-'): v 
                  for k, v in request.META.items() if k.startswith('HTTP_')}
        
        context = self.tracer.extract_context_from_headers(headers)
        
        # Start HTTP server span
        attributes = {
            'http.method': request.method,
            'http.url': request.build_absolute_uri(),
            'http.route': request.path,
            'http.user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            attributes['user.id'] = str(getattr(request.user, 'id', ''))
            attributes['user.email'] = getattr(request.user, 'email', '')
        
        span_name = f"{request.method} {request.path}"
        
        with self.tracer.span(span_name, SpanKind.SERVER, attributes) as span:
            # Store span in request for view access
            request.tracing_span = span
            
            try:
                response = self.get_response(request)
                
                # Add response attributes
                span.set_attribute('http.status_code', response.status_code)
                
                if response.status_code >= 400:
                    span.set_status(SpanStatus.ERROR)
                
                # Inject tracing headers into response
                headers = self.tracer.inject_context_to_headers({})
                for key, value in headers.items():
                    response[key] = value
                
                return response
                
            except Exception as e:
                span.add_event("exception", {
                    'exception.type': type(e).__name__,
                    'exception.message': str(e)
                })
                raise


__all__ = [
    'SpanKind',
    'SpanStatus', 
    'SpanContext',
    'Span',
    'Tracer',
    'TracingContext',
    'TracingMiddleware',
    'get_tracer',
    'trace_operation',
    'trace_http_client',
    'trace_database_operation',
]