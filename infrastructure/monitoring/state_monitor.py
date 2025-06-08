"""
State health monitoring and metrics collection for conversation state management.

Provides comprehensive monitoring, health checks, and alerting capabilities
for the state management infrastructure.
"""

import asyncio
import logging
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis

from domains.shared.models.conversation_state import ConversationState, ConversationStatus
from infrastructure.messaging.state_manager import IConversationStateManager
from infrastructure.messaging.state_recovery import IStateBackupStrategy, IStateCorruptionDetector
from infrastructure.persistence.cache.session_store import ISessionStore

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms
        }


@dataclass
class Metric:
    """Represents a metric measurement"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StateHealthSummary:
    """Summary of state management health"""
    overall_status: HealthStatus
    total_conversations: int
    active_conversations: int
    healthy_conversations: int
    warning_conversations: int
    critical_conversations: int
    avg_response_time_ms: float
    error_rate: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class IHealthCheck(ABC):
    """Interface for health checks"""
    
    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Perform health check and return result"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the health check"""
        pass


class IMetricsCollector(ABC):
    """Interface for metrics collection"""
    
    @abstractmethod
    async def record_metric(self, metric: Metric) -> None:
        """Record a metric"""
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        name_pattern: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get recorded metrics"""
        pass


class RedisConnectionHealthCheck(IHealthCheck):
    """Health check for Redis connection"""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize with Redis client"""
        self.redis_client = redis_client
    
    @property
    def name(self) -> str:
        return "redis_connection"
    
    async def check(self) -> HealthCheckResult:
        """Check Redis connection health"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            await self.redis_client.ping()
            
            # Test read/write operations
            test_key = "health_check_test"
            test_value = str(int(time.time()))
            
            await self.redis_client.setex(test_key, 10, test_value)
            retrieved_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            if retrieved_value.decode() != test_value:
                raise Exception("Read/write test failed")
            
            # Get Redis info
            info = await self.redis_client.info()
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Redis connection is healthy",
                details={
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                },
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Redis connection failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )


class StateManagerHealthCheck(IHealthCheck):
    """Health check for state manager operations"""
    
    def __init__(self, state_manager: IConversationStateManager):
        """Initialize with state manager"""
        self.state_manager = state_manager
    
    @property
    def name(self) -> str:
        return "state_manager"
    
    async def check(self) -> HealthCheckResult:
        """Check state manager health"""
        start_time = time.time()
        
        try:
            # Test basic operations
            test_user_id = f"health_check_{int(time.time())}"
            
            # Create test conversation
            conversation = await self.state_manager.create_conversation(
                user_id=test_user_id,
                ttl_seconds=60
            )
            
            conversation_id = conversation.conversation_id
            
            # Test retrieval
            retrieved = await self.state_manager.get_conversation(conversation_id)
            if not retrieved:
                raise Exception("Failed to retrieve created conversation")
            
            # Test update
            from domains.shared.models.conversation_state import ConversationStateDelta
            delta = ConversationStateDelta(
                conversation_id=conversation_id,
                operation="update_metadata",
                changes={"metadata": {"health_check": True}}
            )
            
            update_success = await self.state_manager.update_conversation(conversation_id, delta)
            if not update_success:
                raise Exception("Failed to update conversation")
            
            # Cleanup
            await self.state_manager.delete_conversation(conversation_id)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="State manager is operating correctly",
                details={
                    "operations_tested": ["create", "get", "update", "delete"],
                    "test_conversation_id": conversation_id
                },
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"State manager check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )


class BackupSystemHealthCheck(IHealthCheck):
    """Health check for backup system"""
    
    def __init__(self, backup_strategy: IStateBackupStrategy):
        """Initialize with backup strategy"""
        self.backup_strategy = backup_strategy
    
    @property
    def name(self) -> str:
        return "backup_system"
    
    async def check(self) -> HealthCheckResult:
        """Check backup system health"""
        start_time = time.time()
        
        try:
            # Create test conversation state
            from domains.shared.models.conversation_state import ConversationState, ConversationContext
            
            test_conversation = ConversationState(
                user_id=f"backup_health_check_{int(time.time())}"
            )
            test_conversation.add_user_message("Health check test message")
            
            # Test backup creation
            from infrastructure.messaging.state_recovery import BackupType
            version = await self.backup_strategy.create_backup(
                test_conversation,
                BackupType.FULL,
                {"health_check": True}
            )
            
            # Test backup retrieval
            recovery_result = await self.backup_strategy.restore_backup(
                test_conversation.conversation_id,
                version.version_id
            )
            
            if not recovery_result.is_successful():
                raise Exception(f"Backup restoration failed: {recovery_result.errors}")
            
            # Cleanup
            await self.backup_strategy.delete_version(
                test_conversation.conversation_id,
                version.version_id
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Backup system is functioning correctly",
                details={
                    "backup_version": version.version_id,
                    "backup_size": version.size_bytes,
                    "recovery_time": recovery_result.recovery_time_ms
                },
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Backup system check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )


class ConversationHealthCheck(IHealthCheck):
    """Health check for conversation states"""
    
    def __init__(
        self,
        state_manager: IConversationStateManager,
        corruption_detector: IStateCorruptionDetector,
        max_conversations_to_check: int = 50
    ):
        """Initialize with state manager and corruption detector"""
        self.state_manager = state_manager
        self.corruption_detector = corruption_detector
        self.max_conversations_to_check = max_conversations_to_check
    
    @property
    def name(self) -> str:
        return "conversation_health"
    
    async def check(self) -> HealthCheckResult:
        """Check health of conversation states"""
        start_time = time.time()
        
        try:
            # Get sample of conversations to check
            # This is a simplified implementation - in practice, you'd need to
            # implement a way to scan conversations in the state manager
            
            conversations_checked = 0
            healthy_count = 0
            warning_count = 0
            critical_count = 0
            issues_found = []
            
            # For demonstration, we'll create a mock check
            # In practice, this would scan actual conversations
            
            duration_ms = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            if critical_count > 0:
                status = HealthStatus.CRITICAL
            elif warning_count > 0:
                status = HealthStatus.WARNING
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=f"Checked {conversations_checked} conversations",
                details={
                    "conversations_checked": conversations_checked,
                    "healthy": healthy_count,
                    "warnings": warning_count,
                    "critical": critical_count,
                    "issues": issues_found[:10]  # Limit to first 10 issues
                },
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Conversation health check failed: {e}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )


class RedisMetricsCollector(IMetricsCollector):
    """Redis-based metrics collector"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "metrics:",
        retention_days: int = 7
    ):
        """Initialize with Redis client"""
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.retention_seconds = retention_days * 24 * 3600
    
    def _get_metric_key(self, metric_name: str) -> str:
        """Get Redis key for metric"""
        return f"{self.key_prefix}{metric_name}"
    
    async def record_metric(self, metric: Metric) -> None:
        """Record a metric in Redis"""
        try:
            metric_key = self._get_metric_key(metric.name)
            
            # Store metric with timestamp as score in sorted set
            timestamp_score = metric.timestamp.timestamp()
            metric_data = json.dumps(metric.to_dict())
            
            await self.redis_client.zadd(metric_key, {metric_data: timestamp_score})
            
            # Set TTL on the key
            await self.redis_client.expire(metric_key, self.retention_seconds)
            
            # Remove old entries (older than retention period)
            cutoff_time = (datetime.utcnow() - timedelta(seconds=self.retention_seconds)).timestamp()
            await self.redis_client.zremrangebyscore(metric_key, 0, cutoff_time)
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric.name}: {e}")
    
    async def get_metrics(
        self,
        name_pattern: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get recorded metrics"""
        try:
            metrics = []
            
            # Determine which keys to check
            if name_pattern:
                pattern = f"{self.key_prefix}{name_pattern}"
            else:
                pattern = f"{self.key_prefix}*"
            
            # Scan for metric keys
            async for key in self.redis_client.scan_iter(match=pattern, count=100):
                key_str = key.decode() if isinstance(key, bytes) else key
                
                # Determine time range
                min_score = since.timestamp() if since else "-inf"
                max_score = "+inf"
                
                # Get metrics from sorted set
                metric_data_list = await self.redis_client.zrangebyscore(
                    key_str, min_score, max_score, start=0, num=limit
                )
                
                for metric_data in metric_data_list:
                    try:
                        metric_dict = json.loads(metric_data)
                        metric = Metric(
                            name=metric_dict["name"],
                            type=MetricType(metric_dict["type"]),
                            value=metric_dict["value"],
                            labels=metric_dict["labels"],
                            timestamp=datetime.fromisoformat(metric_dict["timestamp"])
                        )
                        metrics.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse metric data: {e}")
                
                if len(metrics) >= limit:
                    break
            
            # Sort by timestamp
            metrics.sort(key=lambda m: m.timestamp, reverse=True)
            return metrics[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []


class StateHealthMonitor:
    """
    Main state health monitoring system.
    
    Coordinates health checks, metrics collection, and alerting for
    the conversation state management infrastructure.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        state_manager: IConversationStateManager,
        backup_strategy: Optional[IStateBackupStrategy] = None,
        corruption_detector: Optional[IStateCorruptionDetector] = None,
        check_interval_seconds: int = 300,  # 5 minutes
        alert_callback: Optional[Callable[[HealthCheckResult], None]] = None
    ):
        """
        Initialize state health monitor
        
        Args:
            redis_client: Redis client for health checks and metrics
            state_manager: State manager to monitor
            backup_strategy: Optional backup strategy to monitor
            corruption_detector: Optional corruption detector
            check_interval_seconds: Interval between health checks
            alert_callback: Optional callback for alerts
        """
        self.redis_client = redis_client
        self.state_manager = state_manager
        self.backup_strategy = backup_strategy
        self.corruption_detector = corruption_detector
        self.check_interval = check_interval_seconds
        self.alert_callback = alert_callback
        
        # Initialize collectors and checks
        self.metrics_collector = RedisMetricsCollector(redis_client)
        self.health_checks: List[IHealthCheck] = []
        
        # Setup default health checks
        self._setup_health_checks()
        
        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_health_summary: Optional[StateHealthSummary] = None
    
    def _setup_health_checks(self):
        """Setup default health checks"""
        # Redis connection check
        self.health_checks.append(RedisConnectionHealthCheck(self.redis_client))
        
        # State manager check
        self.health_checks.append(StateManagerHealthCheck(self.state_manager))
        
        # Backup system check (if available)
        if self.backup_strategy:
            self.health_checks.append(BackupSystemHealthCheck(self.backup_strategy))
        
        # Conversation health check (if corruption detector available)
        if self.corruption_detector:
            self.health_checks.append(ConversationHealthCheck(
                self.state_manager, self.corruption_detector
            ))
    
    def add_health_check(self, health_check: IHealthCheck):
        """Add a custom health check"""
        self.health_checks.append(health_check)
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {},
            timestamp=datetime.utcnow()
        )
        await self.metrics_collector.record_metric(metric)
    
    async def run_health_checks(self) -> List[HealthCheckResult]:
        """Run all health checks and return results"""
        results = []
        
        for health_check in self.health_checks:
            try:
                result = await health_check.check()
                results.append(result)
                
                # Record health check metrics
                await self.record_metric(
                    f"health_check_{health_check.name}_duration",
                    result.duration_ms,
                    MetricType.TIMER,
                    {"status": result.status.value}
                )
                
                # Alert if critical
                if result.status == HealthStatus.CRITICAL and self.alert_callback:
                    try:
                        self.alert_callback(result)
                    except Exception as e:
                        logger.error(f"Alert callback failed: {e}")
                
            except Exception as e:
                logger.error(f"Health check {health_check.name} failed: {e}")
                
                error_result = HealthCheckResult(
                    name=health_check.name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check execution failed: {e}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow(),
                    duration_ms=0
                )
                results.append(error_result)
        
        return results
    
    async def get_health_summary(self) -> StateHealthSummary:
        """Get overall health summary"""
        try:
            # Run health checks
            check_results = await self.run_health_checks()
            
            # Determine overall status
            overall_status = HealthStatus.HEALTHY
            critical_count = sum(1 for r in check_results if r.status == HealthStatus.CRITICAL)
            warning_count = sum(1 for r in check_results if r.status == HealthStatus.WARNING)
            
            if critical_count > 0:
                overall_status = HealthStatus.CRITICAL
            elif warning_count > 0:
                overall_status = HealthStatus.WARNING
            
            # Get metrics for additional insights
            response_time_metrics = await self.metrics_collector.get_metrics(
                name_pattern="health_check_*_duration",
                since=datetime.utcnow() - timedelta(hours=1),
                limit=100
            )
            
            avg_response_time = 0.0
            if response_time_metrics:
                avg_response_time = sum(m.value for m in response_time_metrics) / len(response_time_metrics)
            
            # Calculate error rate (simplified)
            error_rate = critical_count / len(check_results) if check_results else 0.0
            
            # Create summary
            summary = StateHealthSummary(
                overall_status=overall_status,
                total_conversations=0,  # Would need to implement conversation counting
                active_conversations=0,  # Would need to implement active conversation detection
                healthy_conversations=0,  # Would need conversation health analysis
                warning_conversations=0,
                critical_conversations=0,
                avg_response_time_ms=avg_response_time,
                error_rate=error_rate,
                last_updated=datetime.utcnow()
            )
            
            self._last_health_summary = summary
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate health summary: {e}")
            
            return StateHealthSummary(
                overall_status=HealthStatus.UNKNOWN,
                total_conversations=0,
                active_conversations=0,
                healthy_conversations=0,
                warning_conversations=0,
                critical_conversations=0,
                avg_response_time_ms=0.0,
                error_rate=1.0,
                last_updated=datetime.utcnow()
            )
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self._monitoring:
            logger.warning("Monitoring is already running")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started health monitoring with {self.check_interval}s interval")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self._monitoring:
                try:
                    # Run health checks and generate summary
                    summary = await self.get_health_summary()
                    
                    # Record summary metrics
                    await self.record_metric(
                        "state_health_overall_status",
                        1.0 if summary.overall_status == HealthStatus.HEALTHY else 0.0,
                        MetricType.GAUGE
                    )
                    
                    await self.record_metric(
                        "state_health_error_rate",
                        summary.error_rate,
                        MetricType.GAUGE
                    )
                    
                    await self.record_metric(
                        "state_health_avg_response_time",
                        summary.avg_response_time_ms,
                        MetricType.GAUGE
                    )
                    
                    logger.debug(f"Health monitoring cycle completed: {summary.overall_status.value}")
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop failed: {e}")
    
    async def get_metrics_report(
        self,
        since: Optional[datetime] = None,
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get metrics report"""
        try:
            if since is None:
                since = datetime.utcnow() - timedelta(hours=24)
            
            report = {
                "period_start": since.isoformat(),
                "period_end": datetime.utcnow().isoformat(),
                "metrics": {}
            }
            
            # Get metrics
            if metric_names:
                for metric_name in metric_names:
                    metrics = await self.metrics_collector.get_metrics(
                        name_pattern=metric_name,
                        since=since,
                        limit=1000
                    )
                    report["metrics"][metric_name] = [m.to_dict() for m in metrics]
            else:
                # Get all metrics
                all_metrics = await self.metrics_collector.get_metrics(since=since, limit=1000)
                
                # Group by metric name
                by_name = {}
                for metric in all_metrics:
                    if metric.name not in by_name:
                        by_name[metric.name] = []
                    by_name[metric.name].append(metric.to_dict())
                
                report["metrics"] = by_name
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate metrics report: {e}")
            return {"error": str(e)}


class StateMonitorFactory:
    """Factory for creating state monitoring components"""
    
    @staticmethod
    def create_health_monitor(
        redis_client: redis.Redis,
        state_manager: IConversationStateManager,
        backup_strategy: Optional[IStateBackupStrategy] = None,
        corruption_detector: Optional[IStateCorruptionDetector] = None,
        check_interval_seconds: int = 300
    ) -> StateHealthMonitor:
        """Create state health monitor with default configuration"""
        return StateHealthMonitor(
            redis_client=redis_client,
            state_manager=state_manager,
            backup_strategy=backup_strategy,
            corruption_detector=corruption_detector,
            check_interval_seconds=check_interval_seconds
        )
    
    @staticmethod
    def create_metrics_collector(redis_client: redis.Redis) -> RedisMetricsCollector:
        """Create Redis metrics collector"""
        return RedisMetricsCollector(redis_client)