"""
Application metrics collection infrastructure.

Provides a comprehensive metrics system for tracking application performance,
business KPIs, and operational metrics with support for counters, histograms,
and gauges.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from enum import Enum


class MetricType(Enum):
    """Types of metrics supported by the system."""
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


@dataclass
class MetricData:
    """Container for metric data with metadata."""
    name: str
    metric_type: MetricType
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    description: str = ""


class Counter:
    """Thread-safe counter metric that only increases."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self, amount: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the counter by the specified amount."""
        with self._lock:
            self._value += amount
        
        # Record the metric event
        MetricsRegistry.get_instance().record_metric(
            MetricData(
                name=self.name,
                metric_type=MetricType.COUNTER,
                value=amount,
                labels=labels or {},
                description=self.description
            )
        )
    
    def get_value(self) -> Union[int, float]:
        """Get the current counter value."""
        with self._lock:
            return self._value
    
    def reset(self) -> None:
        """Reset the counter to zero."""
        with self._lock:
            self._value = 0


class Histogram:
    """Histogram metric for measuring distributions."""
    
    def __init__(self, name: str, description: str = "", max_samples: int = 1000):
        self.name = name
        self.description = description
        self.max_samples = max_samples
        self._samples = deque(maxlen=max_samples)
        self._lock = threading.Lock()
    
    def observe(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Record a new observation."""
        with self._lock:
            self._samples.append(value)
        
        # Record the metric event
        MetricsRegistry.get_instance().record_metric(
            MetricData(
                name=self.name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                labels=labels or {},
                description=self.description
            )
        )
    
    def get_statistics(self) -> Dict[str, Union[int, float]]:
        """Get statistical summary of the histogram."""
        with self._lock:
            if not self._samples:
                return {
                    'count': 0,
                    'sum': 0,
                    'min': 0,
                    'max': 0,
                    'mean': 0,
                    'p50': 0,
                    'p95': 0,
                    'p99': 0
                }
            
            sorted_samples = sorted(self._samples)
            count = len(sorted_samples)
            total = sum(sorted_samples)
            
            def percentile(data: List[float], p: float) -> float:
                """Calculate percentile."""
                if not data:
                    return 0
                k = (len(data) - 1) * p
                f = int(k)
                c = k - f
                if f + 1 < len(data):
                    return data[f] * (1 - c) + data[f + 1] * c
                return data[f]
            
            return {
                'count': count,
                'sum': total,
                'min': min(sorted_samples),
                'max': max(sorted_samples),
                'mean': total / count,
                'p50': percentile(sorted_samples, 0.5),
                'p95': percentile(sorted_samples, 0.95),
                'p99': percentile(sorted_samples, 0.99)
            }


class Gauge:
    """Gauge metric for current values that can increase or decrease."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0
        self._lock = threading.Lock()
    
    def set(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Set the gauge to a specific value."""
        with self._lock:
            self._value = value
        
        # Record the metric event
        MetricsRegistry.get_instance().record_metric(
            MetricData(
                name=self.name,
                metric_type=MetricType.GAUGE,
                value=value,
                labels=labels or {},
                description=self.description
            )
        )
    
    def increment(self, amount: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the gauge by the specified amount."""
        with self._lock:
            self._value += amount
            new_value = self._value
        
        # Record the metric event
        MetricsRegistry.get_instance().record_metric(
            MetricData(
                name=self.name,
                metric_type=MetricType.GAUGE,
                value=new_value,
                labels=labels or {},
                description=self.description
            )
        )
    
    def decrement(self, amount: Union[int, float] = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement the gauge by the specified amount."""
        self.increment(-amount, labels)
    
    def get_value(self) -> Union[int, float]:
        """Get the current gauge value."""
        with self._lock:
            return self._value


class MetricsRegistry:
    """Singleton registry for managing application metrics."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.metrics: Dict[str, Union[Counter, Histogram, Gauge]] = {}
        self.metric_history: deque = deque(maxlen=10000)  # Keep last 10k metric events
        self._registry_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'MetricsRegistry':
        """Get the singleton instance of MetricsRegistry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def register_counter(self, name: str, description: str = "") -> Counter:
        """Register and return a new counter metric."""
        with self._registry_lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Counter):
                    raise ValueError(f"Metric '{name}' already exists as {type(metric).__name__}")
                return metric
            
            counter = Counter(name, description)
            self.metrics[name] = counter
            return counter
    
    def register_histogram(self, name: str, description: str = "", max_samples: int = 1000) -> Histogram:
        """Register and return a new histogram metric."""
        with self._registry_lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric '{name}' already exists as {type(metric).__name__}")
                return metric
            
            histogram = Histogram(name, description, max_samples)
            self.metrics[name] = histogram
            return histogram
    
    def register_gauge(self, name: str, description: str = "") -> Gauge:
        """Register and return a new gauge metric."""
        with self._registry_lock:
            if name in self.metrics:
                metric = self.metrics[name]
                if not isinstance(metric, Gauge):
                    raise ValueError(f"Metric '{name}' already exists as {type(metric).__name__}")
                return metric
            
            gauge = Gauge(name, description)
            self.metrics[name] = gauge
            return gauge
    
    def record_metric(self, metric_data: MetricData) -> None:
        """Record a metric event in the history."""
        self.metric_history.append(metric_data)
    
    def get_metric(self, name: str) -> Optional[Union[Counter, Histogram, Gauge]]:
        """Get a registered metric by name."""
        with self._registry_lock:
            return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Union[Counter, Histogram, Gauge]]:
        """Get all registered metrics."""
        with self._registry_lock:
            return self.metrics.copy()
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics and their current values."""
        summary = {}
        with self._registry_lock:
            for name, metric in self.metrics.items():
                if isinstance(metric, Counter):
                    summary[name] = {
                        'type': 'counter',
                        'value': metric.get_value(),
                        'description': metric.description
                    }
                elif isinstance(metric, Histogram):
                    summary[name] = {
                        'type': 'histogram',
                        'statistics': metric.get_statistics(),
                        'description': metric.description
                    }
                elif isinstance(metric, Gauge):
                    summary[name] = {
                        'type': 'gauge',
                        'value': metric.get_value(),
                        'description': metric.description
                    }
        return summary
    
    def clear_metrics(self) -> None:
        """Clear all registered metrics (useful for testing)."""
        with self._registry_lock:
            self.metrics.clear()
            self.metric_history.clear()


# Convenience functions for creating metrics
def create_counter(name: str, description: str = "") -> Counter:
    """Create and register a counter metric."""
    return MetricsRegistry.get_instance().register_counter(name, description)


def create_histogram(name: str, description: str = "", max_samples: int = 1000) -> Histogram:
    """Create and register a histogram metric."""
    return MetricsRegistry.get_instance().register_histogram(name, description, max_samples)


def create_gauge(name: str, description: str = "") -> Gauge:
    """Create and register a gauge metric."""
    return MetricsRegistry.get_instance().register_gauge(name, description)


def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of all application metrics."""
    return MetricsRegistry.get_instance().get_metric_summary()


# Pre-defined application metrics
APP_METRICS = {
    # HTTP Request metrics
    'http_requests_total': create_counter(
        'http_requests_total', 
        'Total number of HTTP requests'
    ),
    'http_request_duration': create_histogram(
        'http_request_duration', 
        'HTTP request duration in seconds'
    ),
    'http_errors_total': create_counter(
        'http_errors_total', 
        'Total number of HTTP errors'
    ),
    
    # Authentication metrics
    'auth_attempts_total': create_counter(
        'auth_attempts_total', 
        'Total authentication attempts'
    ),
    'auth_failures_total': create_counter(
        'auth_failures_total', 
        'Total authentication failures'
    ),
    'active_sessions': create_gauge(
        'active_sessions', 
        'Number of active user sessions'
    ),
    
    # Business metrics
    'user_registrations_total': create_counter(
        'user_registrations_total', 
        'Total user registrations'
    ),
    'onboarding_completions_total': create_counter(
        'onboarding_completions_total', 
        'Total onboarding completions'
    ),
    'api_calls_per_user': create_histogram(
        'api_calls_per_user', 
        'Number of API calls per user session'
    ),
    
    # System metrics
    'database_queries_total': create_counter(
        'database_queries_total', 
        'Total database queries'
    ),
    'database_query_duration': create_histogram(
        'database_query_duration', 
        'Database query duration in seconds'
    ),
    'external_api_calls_total': create_counter(
        'external_api_calls_total', 
        'Total external API calls'
    ),
    'external_api_duration': create_histogram(
        'external_api_duration', 
        'External API call duration in seconds'
    ),
}


__all__ = [
    'MetricType',
    'MetricData',
    'Counter',
    'Histogram', 
    'Gauge',
    'MetricsRegistry',
    'create_counter',
    'create_histogram',
    'create_gauge',
    'get_metrics_summary',
    'APP_METRICS',
]