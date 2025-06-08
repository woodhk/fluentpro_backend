"""
Health check infrastructure for system monitoring.

Provides comprehensive health monitoring capabilities including database connectivity,
external service health, resource monitoring, and overall system status checks.
"""

import asyncio
import psutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections
from django.http import JsonResponse
from django.views import View

from infrastructure.monitoring.logging_config import get_logger
from infrastructure.monitoring.metrics import APP_METRICS, get_metrics_summary


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    timestamp: float = field(default_factory=time.time)


class HealthCheck(ABC):
    """Abstract base class for health checks."""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def check(self) -> HealthCheckResult:
        """Perform the health check."""
        pass
    
    def run_check(self) -> HealthCheckResult:
        """Run the health check with timing and error handling."""
        start_time = time.time()
        
        try:
            result = self.check()
            duration_ms = round((time.time() - start_time) * 1000, 2)
            result.duration_ms = duration_ms
            
            self.logger.debug(
                "Health check completed",
                check_name=self.name,
                status=result.status.value,
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            self.logger.error(
                "Health check failed",
                check_name=self.name,
                error=str(e),
                duration_ms=duration_ms
            )
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                details={'exception': str(e)}
            )


class DatabaseHealthCheck(HealthCheck):
    """Health check for database connectivity."""
    
    def __init__(self, db_alias: str = 'default'):
        super().__init__(f"database_{db_alias}")
        self.db_alias = db_alias
    
    def check(self) -> HealthCheckResult:
        """Check database connectivity."""
        try:
            db_conn = connections[self.db_alias]
            
            # Test connection
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result and result[0] == 1:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    details={
                        'database': db_conn.settings_dict.get('NAME', 'unknown'),
                        'engine': db_conn.settings_dict.get('ENGINE', 'unknown')
                    }
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="Database query returned unexpected result"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                details={'error': str(e)}
            )


class CacheHealthCheck(HealthCheck):
    """Health check for cache connectivity."""
    
    def __init__(self):
        super().__init__("cache")
    
    def check(self) -> HealthCheckResult:
        """Check cache connectivity."""
        try:
            test_key = "health_check_test"
            test_value = str(time.time())
            
            # Set a test value
            cache.set(test_key, test_value, timeout=60)
            
            # Retrieve the test value
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                # Clean up
                cache.delete(test_key)
                
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Cache connection successful",
                    details={'backend': str(cache.__class__)}
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="Cache set/get operation failed"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Cache connection failed: {str(e)}",
                details={'error': str(e)}
            )


class ExternalServiceHealthCheck(HealthCheck):
    """Health check for external services."""
    
    def __init__(self, service_name: str, check_url: str, 
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(f"external_service_{service_name}")
        self.service_name = service_name
        self.check_url = check_url
        self.headers = headers or {}
    
    def check(self) -> HealthCheckResult:
        """Check external service health."""
        try:
            import requests
            
            response = requests.get(
                self.check_url, 
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message=f"{self.service_name} service is healthy",
                    details={
                        'url': self.check_url,
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                )
            elif 400 <= response.status_code < 500:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"{self.service_name} service returned client error",
                    details={
                        'url': self.check_url,
                        'status_code': response.status_code
                    }
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"{self.service_name} service returned server error",
                    details={
                        'url': self.check_url,
                        'status_code': response.status_code
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"{self.service_name} service check failed: {str(e)}",
                details={'error': str(e)}
            )


class SystemResourceHealthCheck(HealthCheck):
    """Health check for system resources."""
    
    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0,
                 disk_threshold: float = 90.0):
        super().__init__("system_resources")
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    def check(self) -> HealthCheckResult:
        """Check system resource usage."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            details = {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'disk_percent': round(disk_percent, 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2)
            }
            
            # Determine status
            if (cpu_percent >= self.cpu_threshold or 
                memory_percent >= self.memory_threshold or 
                disk_percent >= self.disk_threshold):
                
                status = HealthStatus.UNHEALTHY
                message = "System resources are critically high"
                
            elif (cpu_percent >= self.cpu_threshold * 0.8 or 
                  memory_percent >= self.memory_threshold * 0.8 or 
                  disk_percent >= self.disk_threshold * 0.8):
                
                status = HealthStatus.DEGRADED
                message = "System resources are elevated"
                
            else:
                status = HealthStatus.HEALTHY
                message = "System resources are normal"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}",
                details={'error': str(e)}
            )


class ApplicationHealthCheck(HealthCheck):
    """Health check for application-specific metrics."""
    
    def __init__(self):
        super().__init__("application")
    
    def check(self) -> HealthCheckResult:
        """Check application health metrics."""
        try:
            # Get metrics summary
            metrics = get_metrics_summary()
            
            # Calculate health indicators
            http_requests = metrics.get('http_requests_total', {}).get('value', 0)
            http_errors = metrics.get('http_errors_total', {}).get('value', 0)
            
            error_rate = 0
            if http_requests > 0:
                error_rate = (http_errors / http_requests) * 100
            
            response_times = metrics.get('http_request_duration', {}).get('statistics', {})
            avg_response_time = response_times.get('mean', 0) * 1000  # Convert to ms
            
            details = {
                'total_requests': http_requests,
                'total_errors': http_errors,
                'error_rate_percent': round(error_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'active_sessions': metrics.get('active_sessions', {}).get('value', 0)
            }
            
            # Determine status based on metrics
            if error_rate > 10 or avg_response_time > 5000:  # 10% error rate or 5s avg response
                status = HealthStatus.UNHEALTHY
                message = "Application performance is poor"
            elif error_rate > 5 or avg_response_time > 2000:  # 5% error rate or 2s avg response
                status = HealthStatus.DEGRADED
                message = "Application performance is degraded"
            else:
                status = HealthStatus.HEALTHY
                message = "Application is performing well"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Application health check failed: {str(e)}",
                details={'error': str(e)}
            )


class HealthCheckRegistry:
    """Registry for managing health checks."""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.logger = get_logger(__name__)
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """Setup default health checks."""
        # Database check
        self.register(DatabaseHealthCheck())
        
        # Cache check
        self.register(CacheHealthCheck())
        
        # System resources check
        self.register(SystemResourceHealthCheck())
        
        # Application metrics check
        self.register(ApplicationHealthCheck())
        
        # External service checks (only if Django is configured)
        try:
            from django.conf import settings
            if hasattr(settings, 'SUPABASE_URL'):
                self.register(ExternalServiceHealthCheck(
                    'supabase',
                    f"{settings.SUPABASE_URL}/rest/v1/",
                    {'apikey': getattr(settings, 'SUPABASE_ANON_KEY', '')}
                ))
        except Exception:
            # Django not configured or settings not available
            pass
    
    def register(self, health_check: HealthCheck) -> None:
        """Register a health check."""
        self.checks[health_check.name] = health_check
        self.logger.debug(f"Registered health check: {health_check.name}")
    
    def unregister(self, name: str) -> None:
        """Unregister a health check."""
        if name in self.checks:
            del self.checks[name]
            self.logger.debug(f"Unregistered health check: {name}")
    
    def run_check(self, name: str) -> Optional[HealthCheckResult]:
        """Run a specific health check."""
        if name in self.checks:
            return self.checks[name].run_check()
        return None
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name, check in self.checks.items():
            results[name] = check.run_check()
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = self.run_all_checks()
        
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


# Global registry instance
_health_registry = HealthCheckRegistry()


def get_health_registry() -> HealthCheckRegistry:
    """Get the global health check registry."""
    return _health_registry


class HealthCheckView(View):
    """Django view for health check endpoints."""
    
    def get(self, request, check_name=None):
        """Handle health check requests."""
        registry = get_health_registry()
        
        if check_name:
            # Run specific health check
            result = registry.run_check(check_name)
            if result:
                return JsonResponse({
                    'name': result.name,
                    'status': result.status.value,
                    'message': result.message,
                    'details': result.details,
                    'duration_ms': result.duration_ms,
                    'timestamp': result.timestamp
                })
            else:
                return JsonResponse({
                    'error': f'Health check "{check_name}" not found'
                }, status=404)
        else:
            # Run all health checks
            results = registry.run_all_checks()
            overall_status = registry.get_overall_status()
            
            response_data = {
                'status': overall_status.value,
                'timestamp': time.time(),
                'checks': {}
            }
            
            for name, result in results.items():
                response_data['checks'][name] = {
                    'status': result.status.value,
                    'message': result.message,
                    'details': result.details,
                    'duration_ms': result.duration_ms
                }
            
            # Set HTTP status based on overall health
            status_code = 200
            if overall_status == HealthStatus.DEGRADED:
                status_code = 503  # Service Unavailable
            elif overall_status == HealthStatus.UNHEALTHY:
                status_code = 503  # Service Unavailable
            
            return JsonResponse(response_data, status=status_code)


class ReadinessCheckView(View):
    """Django view for readiness checks (subset of health checks)."""
    
    def get(self, request):
        """Check if the application is ready to serve requests."""
        registry = get_health_registry()
        
        # Only check critical dependencies for readiness
        critical_checks = ['database_default', 'cache']
        results = {}
        
        for check_name in critical_checks:
            result = registry.run_check(check_name)
            if result:
                results[check_name] = result
        
        # Determine readiness
        all_healthy = all(
            result.status == HealthStatus.HEALTHY 
            for result in results.values()
        )
        
        response_data = {
            'ready': all_healthy,
            'timestamp': time.time(),
            'checks': {
                name: {
                    'status': result.status.value,
                    'message': result.message
                }
                for name, result in results.items()
            }
        }
        
        status_code = 200 if all_healthy else 503
        return JsonResponse(response_data, status=status_code)


class LivenessCheckView(View):
    """Django view for liveness checks."""
    
    def get(self, request):
        """Basic liveness check - just return OK if the application is running."""
        return JsonResponse({
            'alive': True,
            'timestamp': time.time(),
            'service': 'fluentpro_backend'
        })


__all__ = [
    'HealthStatus',
    'HealthCheckResult',
    'HealthCheck',
    'DatabaseHealthCheck',
    'CacheHealthCheck',
    'ExternalServiceHealthCheck',
    'SystemResourceHealthCheck',
    'ApplicationHealthCheck',
    'HealthCheckRegistry',
    'HealthCheckView',
    'ReadinessCheckView',
    'LivenessCheckView',
    'get_health_registry',
]