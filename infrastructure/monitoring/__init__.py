"""
Monitoring infrastructure for state management, health checks, metrics collection,
performance monitoring, distributed tracing, and health monitoring.

Provides comprehensive observability with structured logging, metrics, performance
tracking, distributed tracing, and health check capabilities.
"""

from .logging_config import configure_structlog, get_logger
from .metrics import (
    APP_METRICS,
    MetricsRegistry,
    create_counter,
    create_histogram,
    create_gauge,
    get_metrics_summary
)
from .performance import (
    PerformanceMonitor,
    PerformanceMetrics,
    track_performance,
    track_operation,
    track_database_query,
    track_external_api,
    track_authentication
)
from .tracing import (
    get_tracer,
    trace_operation,
    trace_http_client,
    trace_database_operation,
    TracingMiddleware,
    SpanKind,
    SpanStatus
)
from .health_checks import (
    get_health_registry,
    HealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
    HealthStatus,
    DatabaseHealthCheck,
    CacheHealthCheck,
    ExternalServiceHealthCheck,
    SystemResourceHealthCheck,
    ApplicationHealthCheck
)

__all__ = [
    # Logging
    'configure_structlog',
    'get_logger',
    
    # Metrics
    'APP_METRICS',
    'MetricsRegistry',
    'create_counter',
    'create_histogram',
    'create_gauge',
    'get_metrics_summary',
    
    # Performance
    'PerformanceMonitor',
    'PerformanceMetrics',
    'track_performance',
    'track_operation',
    'track_database_query',
    'track_external_api',
    'track_authentication',
    
    # Tracing
    'get_tracer',
    'trace_operation',
    'trace_http_client',
    'trace_database_operation',
    'TracingMiddleware',
    'SpanKind',
    'SpanStatus',
    
    # Health Checks
    'get_health_registry',
    'HealthCheckView',
    'ReadinessCheckView',
    'LivenessCheckView',
    'HealthStatus',
    'DatabaseHealthCheck',
    'CacheHealthCheck',
    'ExternalServiceHealthCheck',
    'SystemResourceHealthCheck',
    'ApplicationHealthCheck',
]