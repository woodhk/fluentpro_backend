"""
Supabase Connection Pool Management

Provides connection pooling and management for Supabase database connections
to ensure efficient resource utilization and prevent connection exhaustion.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime
import threading
from queue import Queue, Empty, Full
import time


class IConnectionPool(ABC):
    """
    Interface for database connection pooling.
    
    Manages a pool of database connections to improve performance
    and prevent connection exhaustion under load.
    """
    
    @abstractmethod
    def acquire_connection(self, timeout: Optional[float] = None) -> Any:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection (seconds)
            
        Returns:
            Database connection object
            
        Raises:
            ConnectionPoolExhausted: If no connections available within timeout
        """
        pass
    
    @abstractmethod
    def release_connection(self, connection: Any) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: Connection to release
        """
        pass
    
    @abstractmethod
    @contextmanager
    def get_connection(self):
        """
        Context manager for connection acquisition and release.
        
        Usage:
            with pool.get_connection() as conn:
                # Use connection
                pass
        """
        pass
    
    @abstractmethod
    def close_all_connections(self) -> None:
        """Close all connections in the pool."""
        pass
    
    @abstractmethod
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get current pool statistics.
        
        Returns:
            Dict containing:
                - total_connections: Total connections in pool
                - available_connections: Currently available connections
                - in_use_connections: Currently checked out connections
                - wait_queue_size: Number of threads waiting for connections
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check health of connection pool.
        
        Returns:
            True if pool is healthy
        """
        pass


class ISupabaseConnectionPool(IConnectionPool):
    """
    Supabase-specific connection pool interface.
    
    Extends the base connection pool with Supabase-specific features
    like real-time connection management and connection validation.
    """
    
    @abstractmethod
    def acquire_realtime_connection(self, channel: str) -> Any:
        """
        Acquire a connection for real-time subscriptions.
        
        Args:
            channel: Real-time channel name
            
        Returns:
            Real-time connection object
        """
        pass
    
    @abstractmethod
    def validate_connection(self, connection: Any) -> bool:
        """
        Validate that a connection is still active.
        
        Args:
            connection: Connection to validate
            
        Returns:
            True if connection is valid
        """
        pass
    
    @abstractmethod
    def refresh_connection(self, connection: Any) -> Any:
        """
        Refresh a stale connection.
        
        Args:
            connection: Connection to refresh
            
        Returns:
            Refreshed connection or new connection
        """
        pass
    
    @abstractmethod
    def set_connection_timeout(self, timeout: int) -> None:
        """
        Set default connection timeout.
        
        Args:
            timeout: Timeout in seconds
        """
        pass
    
    @abstractmethod
    def get_connection_metrics(self) -> Dict[str, Any]:
        """
        Get detailed connection metrics.
        
        Returns:
            Dict containing:
                - avg_acquisition_time: Average time to acquire connection
                - connection_errors: Number of connection errors
                - connection_timeouts: Number of timeouts
                - total_requests: Total connection requests
                - successful_requests: Successful acquisitions
                - pool_efficiency: Percentage of requests served without waiting
        """
        pass


class ConnectionPoolConfig:
    """Configuration for connection pool."""
    
    def __init__(
        self,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: int = 30,
        idle_timeout: int = 300,
        validation_interval: int = 60,
        retry_attempts: int = 3,
        retry_delay: float = 0.5
    ):
        """
        Initialize connection pool configuration.
        
        Args:
            min_connections: Minimum connections to maintain
            max_connections: Maximum connections allowed
            connection_timeout: Timeout for connection acquisition (seconds)
            idle_timeout: Time before idle connections are closed (seconds)
            validation_interval: Interval between connection validations (seconds)
            retry_attempts: Number of retry attempts for failed connections
            retry_delay: Delay between retry attempts (seconds)
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.validation_interval = validation_interval
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
    
    def validate(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.min_connections < 0:
            raise ValueError("min_connections must be >= 0")
        
        if self.max_connections < self.min_connections:
            raise ValueError("max_connections must be >= min_connections")
        
        if self.connection_timeout <= 0:
            raise ValueError("connection_timeout must be > 0")
        
        if self.idle_timeout <= 0:
            raise ValueError("idle_timeout must be > 0")


class ConnectionPoolException(Exception):
    """Base exception for connection pool errors."""
    pass


class ConnectionPoolExhausted(ConnectionPoolException):
    """Raised when no connections are available."""
    pass


class ConnectionPoolClosed(ConnectionPoolException):
    """Raised when pool is closed."""
    pass


class ConnectionInfo:
    """Information about a pooled connection."""
    
    def __init__(self, connection: Any):
        """
        Initialize connection info.
        
        Args:
            connection: The actual connection object
        """
        self.connection = connection
        self.created_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()
        self.use_count = 0
        self.is_valid = True
    
    def update_usage(self) -> None:
        """Update usage statistics."""
        self.last_used_at = datetime.utcnow()
        self.use_count += 1
    
    def get_idle_time(self) -> float:
        """Get idle time in seconds."""
        return (datetime.utcnow() - self.last_used_at).total_seconds()
    
    def get_age(self) -> float:
        """Get connection age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()