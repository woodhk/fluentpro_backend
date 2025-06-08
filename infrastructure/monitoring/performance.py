"""
Application performance monitoring infrastructure.

Provides performance tracking, monitoring, and alerting capabilities including
response time tracking, error rate monitoring, and performance thresholds.
"""

import functools
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum

from infrastructure.monitoring.logging_config import get_logger
from infrastructure.monitoring.metrics import APP_METRICS, MetricsRegistry


class PerformanceLevel(Enum):
    """Performance level classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    name: str
    warning_threshold: float
    critical_threshold: float
    unit: str = "seconds"
    description: str = ""


@dataclass
class PerformanceAlert:
    """Performance alert data."""
    metric_name: str
    current_value: float
    threshold_value: float
    level: PerformanceLevel
    timestamp: float
    context: Dict[str, Any]


class PerformanceTracker:
    """Context manager for tracking operation performance."""
    
    def __init__(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time = None
        self.end_time = None
        self.logger = get_logger(__name__)
    
    def __enter__(self) -> 'PerformanceTracker':
        """Start performance tracking."""
        self.start_time = time.time()
        self.logger.debug(
            "Performance tracking started",
            operation=self.operation_name,
            labels=self.labels
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End performance tracking and record metrics."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Record performance metrics
        APP_METRICS['http_request_duration'].observe(duration, self.labels)
        
        # Log performance results
        if exc_type is None:
            self.logger.info(
                "Operation completed",
                operation=self.operation_name,
                duration_ms=round(duration * 1000, 2),
                labels=self.labels,
                status="success"
            )
        else:
            self.logger.error(
                "Operation failed",
                operation=self.operation_name,
                duration_ms=round(duration * 1000, 2),
                labels=self.labels,
                status="error",
                exception_type=exc_type.__name__ if exc_type else None
            )
            
            # Record error metrics
            APP_METRICS['http_errors_total'].increment(1, self.labels)
        
        # Check performance thresholds
        PerformanceMonitor.get_instance().check_thresholds(
            self.operation_name, duration, self.labels
        )
    
    def get_duration(self) -> Optional[float]:
        """Get the operation duration if completed."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class PerformanceMonitor:
    """Singleton performance monitor for threshold checking and alerting."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: List[PerformanceAlert] = []
        self.alert_handlers: List[Callable[[PerformanceAlert], None]] = []
        self.logger = get_logger(__name__)
        self._setup_default_thresholds()
    
    @classmethod
    def get_instance(cls) -> 'PerformanceMonitor':
        """Get the singleton instance of PerformanceMonitor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _setup_default_thresholds(self) -> None:
        """Setup default performance thresholds."""
        self.thresholds.update({
            'http_request': PerformanceThreshold(
                name='http_request',
                warning_threshold=1.0,  # 1 second
                critical_threshold=5.0,  # 5 seconds
                unit='seconds',
                description='HTTP request response time'
            ),
            'database_query': PerformanceThreshold(
                name='database_query',
                warning_threshold=0.1,  # 100ms
                critical_threshold=1.0,  # 1 second
                unit='seconds',
                description='Database query execution time'
            ),
            'external_api': PerformanceThreshold(
                name='external_api',
                warning_threshold=2.0,  # 2 seconds
                critical_threshold=10.0,  # 10 seconds
                unit='seconds',
                description='External API call response time'
            ),
            'authentication': PerformanceThreshold(
                name='authentication',
                warning_threshold=0.5,  # 500ms
                critical_threshold=2.0,  # 2 seconds
                unit='seconds',
                description='Authentication process time'
            ),
        })
    
    def add_threshold(self, threshold: PerformanceThreshold) -> None:
        """Add a custom performance threshold."""
        self.thresholds[threshold.name] = threshold
    
    def check_thresholds(self, operation_name: str, duration: float, 
                        context: Optional[Dict[str, Any]] = None) -> None:
        """Check if operation duration exceeds thresholds."""
        context = context or {}
        
        # Find applicable threshold
        threshold = None
        for threshold_name, threshold_config in self.thresholds.items():
            if threshold_name in operation_name.lower():
                threshold = threshold_config
                break
        
        if not threshold:
            return
        
        # Check thresholds
        level = None
        threshold_value = None
        
        if duration >= threshold.critical_threshold:
            level = PerformanceLevel.CRITICAL
            threshold_value = threshold.critical_threshold
        elif duration >= threshold.warning_threshold:
            level = PerformanceLevel.POOR
            threshold_value = threshold.warning_threshold
        
        if level:
            alert = PerformanceAlert(
                metric_name=operation_name,
                current_value=duration,
                threshold_value=threshold_value,
                level=level,
                timestamp=time.time(),
                context=context
            )
            
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        self.alerts.append(alert)
        
        # Log the alert
        self.logger.warning(
            "Performance threshold exceeded",
            metric_name=alert.metric_name,
            current_value=round(alert.current_value * 1000, 2),  # Convert to ms
            threshold_value=round(alert.threshold_value * 1000, 2),  # Convert to ms
            level=alert.level.value,
            context=alert.context
        )
        
        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(
                    "Alert handler failed",
                    handler=handler.__name__,
                    error=str(e)
                )
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]) -> None:
        """Add a custom alert handler."""
        self.alert_handlers.append(handler)
    
    def get_recent_alerts(self, limit: int = 100) -> List[PerformanceAlert]:
        """Get recent performance alerts."""
        return self.alerts[-limit:]
    
    def clear_alerts(self) -> None:
        """Clear all stored alerts."""
        self.alerts.clear()


def track_performance(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator for automatic performance tracking."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTracker(operation_name, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextmanager
def track_operation(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for tracking operation performance."""
    with PerformanceTracker(operation_name, labels) as tracker:
        yield tracker


def track_database_query(query_type: str = "unknown"):
    """Decorator specifically for database query performance tracking."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            labels = {'query_type': query_type}
            with PerformanceTracker(f"database_query_{query_type}", labels):
                APP_METRICS['database_queries_total'].increment(1, labels)
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


def track_external_api(service_name: str, endpoint: str = "unknown"):
    """Decorator for external API call performance tracking."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            labels = {'service': service_name, 'endpoint': endpoint}
            with PerformanceTracker(f"external_api_{service_name}", labels):
                APP_METRICS['external_api_calls_total'].increment(1, labels)
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


def track_authentication(auth_type: str = "standard"):
    """Decorator for authentication performance tracking."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            labels = {'auth_type': auth_type}
            with PerformanceTracker(f"authentication_{auth_type}", labels):
                APP_METRICS['auth_attempts_total'].increment(1, labels)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    APP_METRICS['auth_failures_total'].increment(1, labels)
                    raise
        return wrapper
    return decorator


class PerformanceMetrics:
    """Helper class for common performance metric operations."""
    
    @staticmethod
    def record_response_time(duration: float, status_code: int, 
                           endpoint: str, method: str = "GET") -> None:
        """Record HTTP response time metrics."""
        labels = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        }
        
        APP_METRICS['http_requests_total'].increment(1, labels)
        APP_METRICS['http_request_duration'].observe(duration, labels)
        
        if status_code >= 400:
            APP_METRICS['http_errors_total'].increment(1, labels)
    
    @staticmethod
    def record_user_action(action: str, user_id: Optional[str] = None) -> None:
        """Record user action metrics."""
        labels = {'action': action}
        if user_id:
            labels['user_id'] = user_id
        
        if action == 'registration':
            APP_METRICS['user_registrations_total'].increment(1, labels)
        elif action == 'onboarding_complete':
            APP_METRICS['onboarding_completions_total'].increment(1, labels)
    
    @staticmethod
    def update_active_sessions(count: int) -> None:
        """Update active sessions gauge."""
        APP_METRICS['active_sessions'].set(count)
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """Get a summary of key performance metrics."""
        metrics_summary = MetricsRegistry.get_instance().get_metric_summary()
        
        # Calculate derived metrics
        summary = {
            'response_times': metrics_summary.get('http_request_duration', {}),
            'total_requests': metrics_summary.get('http_requests_total', {}).get('value', 0),
            'total_errors': metrics_summary.get('http_errors_total', {}).get('value', 0),
            'active_sessions': metrics_summary.get('active_sessions', {}).get('value', 0),
            'database_queries': metrics_summary.get('database_queries_total', {}).get('value', 0),
            'external_api_calls': metrics_summary.get('external_api_calls_total', {}).get('value', 0),
        }
        
        # Calculate error rate
        total_requests = summary['total_requests']
        total_errors = summary['total_errors']
        if total_requests > 0:
            summary['error_rate'] = round((total_errors / total_requests) * 100, 2)
        else:
            summary['error_rate'] = 0
        
        return summary


__all__ = [
    'PerformanceLevel',
    'PerformanceThreshold',
    'PerformanceAlert',
    'PerformanceTracker',
    'PerformanceMonitor',
    'track_performance',
    'track_operation',
    'track_database_query',
    'track_external_api',
    'track_authentication',
    'PerformanceMetrics',
]