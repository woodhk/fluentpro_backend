"""WebSocket connection manager for tracking active connections."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Set, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about an active WebSocket connection."""
    channel_name: str
    user_id: str
    user_email: str
    connected_at: datetime
    last_activity: datetime
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert connection info to dictionary."""
        return {
            'channel_name': self.channel_name,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'connected_at': self.connected_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'metadata': self.metadata
        }


class ConnectionManager:
    """
    Manages active WebSocket connections.
    
    Tracks multiple connections per user and provides methods for
    connection lifecycle management and message routing.
    """
    
    def __init__(self):
        # user_id -> set of channel_names
        self._user_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # channel_name -> ConnectionInfo
        self._connections: Dict[str, ConnectionInfo] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info("ConnectionManager initialized")
    
    async def add_connection(
        self, 
        channel_name: str, 
        user_id: str, 
        user_email: str,
        metadata: Dict = None
    ) -> ConnectionInfo:
        """
        Add a new WebSocket connection.
        
        Args:
            channel_name: Unique channel identifier
            user_id: User identifier (Auth0 sub)
            user_email: User email
            metadata: Optional connection metadata
            
        Returns:
            ConnectionInfo object for the new connection
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            
            connection_info = ConnectionInfo(
                channel_name=channel_name,
                user_id=user_id,
                user_email=user_email,
                connected_at=now,
                last_activity=now,
                metadata=metadata or {}
            )
            
            # Add to connections tracking
            self._connections[channel_name] = connection_info
            self._user_connections[user_id].add(channel_name)
            
            logger.info(f"Added connection {channel_name} for user {user_email} ({user_id})")
            logger.info(f"User {user_email} now has {len(self._user_connections[user_id])} active connections")
            
            return connection_info
    
    async def remove_connection(self, channel_name: str) -> Optional[ConnectionInfo]:
        """
        Remove a WebSocket connection.
        
        Args:
            channel_name: Channel to remove
            
        Returns:
            ConnectionInfo of removed connection, or None if not found
        """
        async with self._lock:
            connection_info = self._connections.get(channel_name)
            
            if not connection_info:
                logger.warning(f"Attempted to remove non-existent connection: {channel_name}")
                return None
            
            user_id = connection_info.user_id
            
            # Remove from tracking
            del self._connections[channel_name]
            self._user_connections[user_id].discard(channel_name)
            
            # Clean up empty user sets
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]
            
            logger.info(f"Removed connection {channel_name} for user {connection_info.user_email}")
            
            remaining_connections = len(self._user_connections.get(user_id, set()))
            if remaining_connections > 0:
                logger.info(f"User {connection_info.user_email} still has {remaining_connections} active connections")
            else:
                logger.info(f"User {connection_info.user_email} has no remaining connections")
            
            return connection_info
    
    async def get_connection(self, channel_name: str) -> Optional[ConnectionInfo]:
        """
        Get connection information by channel name.
        
        Args:
            channel_name: Channel to lookup
            
        Returns:
            ConnectionInfo if found, None otherwise
        """
        async with self._lock:
            return self._connections.get(channel_name)
    
    async def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """
        Get all connections for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of ConnectionInfo objects for the user
        """
        async with self._lock:
            channel_names = self._user_connections.get(user_id, set())
            return [
                self._connections[channel_name] 
                for channel_name in channel_names 
                if channel_name in self._connections
            ]
    
    async def get_user_channel_names(self, user_id: str) -> Set[str]:
        """
        Get all channel names for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of channel names
        """
        async with self._lock:
            return self._user_connections.get(user_id, set()).copy()
    
    async def update_connection_activity(self, channel_name: str) -> bool:
        """
        Update the last activity timestamp for a connection.
        
        Args:
            channel_name: Channel to update
            
        Returns:
            True if connection was found and updated, False otherwise
        """
        async with self._lock:
            connection_info = self._connections.get(channel_name)
            
            if connection_info:
                connection_info.update_activity()
                return True
            
            return False
    
    async def update_connection_metadata(
        self, 
        channel_name: str, 
        metadata: Dict
    ) -> bool:
        """
        Update metadata for a connection.
        
        Args:
            channel_name: Channel to update
            metadata: New metadata to merge
            
        Returns:
            True if connection was found and updated, False otherwise
        """
        async with self._lock:
            connection_info = self._connections.get(channel_name)
            
            if connection_info:
                connection_info.metadata.update(metadata)
                connection_info.update_activity()
                return True
            
            return False
    
    async def is_user_connected(self, user_id: str) -> bool:
        """
        Check if a user has any active connections.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active connections, False otherwise
        """
        async with self._lock:
            return bool(self._user_connections.get(user_id))
    
    async def get_connection_count(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Total connection count
        """
        async with self._lock:
            return len(self._connections)
    
    async def get_user_count(self) -> int:
        """
        Get number of unique users with active connections.
        
        Returns:
            Unique user count
        """
        async with self._lock:
            return len(self._user_connections)
    
    async def get_stats(self) -> Dict:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        async with self._lock:
            total_connections = len(self._connections)
            unique_users = len(self._user_connections)
            
            # Calculate average connections per user
            avg_connections_per_user = (
                total_connections / unique_users 
                if unique_users > 0 else 0
            )
            
            # Find user with most connections
            max_connections = 0
            max_user_id = None
            
            for user_id, channels in self._user_connections.items():
                if len(channels) > max_connections:
                    max_connections = len(channels)
                    max_user_id = user_id
            
            return {
                'total_connections': total_connections,
                'unique_users': unique_users,
                'average_connections_per_user': round(avg_connections_per_user, 2),
                'max_connections_per_user': max_connections,
                'max_connections_user_id': max_user_id
            }
    
    async def cleanup_stale_connections(self, max_idle_minutes: int = 60) -> int:
        """
        Remove connections that have been idle for too long.
        
        Args:
            max_idle_minutes: Maximum idle time in minutes
            
        Returns:
            Number of connections cleaned up
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            stale_channels = []
            
            for channel_name, connection_info in self._connections.items():
                idle_minutes = (now - connection_info.last_activity).total_seconds() / 60
                
                if idle_minutes > max_idle_minutes:
                    stale_channels.append(channel_name)
            
            # Remove stale connections
            cleaned_count = 0
            for channel_name in stale_channels:
                connection_info = self._connections.get(channel_name)
                if connection_info:
                    user_id = connection_info.user_id
                    del self._connections[channel_name]
                    self._user_connections[user_id].discard(channel_name)
                    
                    # Clean up empty user sets
                    if not self._user_connections[user_id]:
                        del self._user_connections[user_id]
                    
                    cleaned_count += 1
                    logger.info(f"Cleaned up stale connection {channel_name}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} stale connections")
            
            return cleaned_count
    
    async def get_all_connections(self) -> List[ConnectionInfo]:
        """
        Get all active connections.
        
        Returns:
            List of all ConnectionInfo objects
        """
        async with self._lock:
            return list(self._connections.values())


# Global singleton instance
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global ConnectionManager instance.
    
    Returns:
        ConnectionManager singleton
    """
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    
    return _connection_manager