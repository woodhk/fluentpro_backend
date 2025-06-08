"""WebSocket session manager for persistent session state."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from .connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """WebSocket session data."""
    session_id: str
    user_id: str
    user_email: str
    created_at: datetime
    last_accessed: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.metadata is None:
            self.metadata = {}
    
    def update_access_time(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert session data to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create SessionData from dictionary."""
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            user_email=data['user_email'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            last_accessed=datetime.fromisoformat(data['last_accessed'].replace('Z', '+00:00')),
            data=data.get('data', {}),
            metadata=data.get('metadata', {})
        )


class SessionManager:
    """
    Manages WebSocket sessions with persistence.
    
    Provides session state management that can survive connection
    drops and server restarts.
    """
    
    def __init__(self, session_timeout_hours: int = 24):
        """
        Initialize session manager.
        
        Args:
            session_timeout_hours: Hours after which inactive sessions expire
        """
        # In-memory session storage (could be replaced with Redis/DB)
        self._sessions: Dict[str, SessionData] = {}
        
        # user_id -> session_id mapping for quick lookups
        self._user_sessions: Dict[str, str] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Session timeout
        self._session_timeout = timedelta(hours=session_timeout_hours)
        
        # Connection manager reference
        self._connection_manager = get_connection_manager()
        
        logger.info(f"SessionManager initialized with {session_timeout_hours}h timeout")
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        user_email: str,
        initial_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> SessionData:
        """
        Create a new WebSocket session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier (Auth0 sub)
            user_email: User email
            initial_data: Initial session data
            metadata: Session metadata
            
        Returns:
            SessionData object
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                user_email=user_email,
                created_at=now,
                last_accessed=now,
                data=initial_data or {},
                metadata=metadata or {}
            )
            
            # Store session
            self._sessions[session_id] = session_data
            self._user_sessions[user_id] = session_id
            
            logger.info(f"Created session {session_id} for user {user_email}")
            
            return session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionData if found and valid, None otherwise
        """
        async with self._lock:
            session_data = self._sessions.get(session_id)
            
            if not session_data:
                return None
            
            # Check if session has expired
            if self._is_session_expired(session_data):
                await self._remove_session_internal(session_id)
                return None
            
            # Update access time
            session_data.update_access_time()
            
            return session_data
    
    async def get_user_session(self, user_id: str) -> Optional[SessionData]:
        """
        Get session for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            SessionData if found and valid, None otherwise
        """
        async with self._lock:
            session_id = self._user_sessions.get(user_id)
            
            if not session_id:
                return None
            
            # Use get_session to handle expiration and access time update
            return await self.get_session(session_id)
    
    async def update_session_data(
        self,
        session_id: str,
        data_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            data_updates: Dictionary of data to update
            
        Returns:
            True if session was found and updated, False otherwise
        """
        async with self._lock:
            session_data = self._sessions.get(session_id)
            
            if not session_data or self._is_session_expired(session_data):
                return False
            
            # Update data
            session_data.data.update(data_updates)
            session_data.update_access_time()
            
            logger.debug(f"Updated session {session_id} data: {list(data_updates.keys())}")
            
            return True
    
    async def set_session_data(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Set a specific key-value pair in session data.
        
        Args:
            session_id: Session identifier
            key: Data key
            value: Data value
            
        Returns:
            True if session was found and updated, False otherwise
        """
        return await self.update_session_data(session_id, {key: value})
    
    async def get_session_data(
        self,
        session_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get a specific value from session data.
        
        Args:
            session_id: Session identifier
            key: Data key
            default: Default value if key not found
            
        Returns:
            Value for the key, or default if not found
        """
        session_data = await self.get_session(session_id)
        
        if not session_data:
            return default
        
        return session_data.data.get(key, default)
    
    async def update_session_metadata(
        self,
        session_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update session metadata.
        
        Args:
            session_id: Session identifier
            metadata_updates: Dictionary of metadata to update
            
        Returns:
            True if session was found and updated, False otherwise
        """
        async with self._lock:
            session_data = self._sessions.get(session_id)
            
            if not session_data or self._is_session_expired(session_data):
                return False
            
            # Update metadata
            session_data.metadata.update(metadata_updates)
            session_data.update_access_time()
            
            logger.debug(f"Updated session {session_id} metadata: {list(metadata_updates.keys())}")
            
            return True
    
    async def remove_session(self, session_id: str) -> bool:
        """
        Remove a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and removed, False otherwise
        """
        async with self._lock:
            return await self._remove_session_internal(session_id)
    
    async def _remove_session_internal(self, session_id: str) -> bool:
        """Internal method to remove session (assumes lock is held)."""
        session_data = self._sessions.get(session_id)
        
        if not session_data:
            return False
        
        user_id = session_data.user_id
        
        # Remove session
        del self._sessions[session_id]
        
        # Remove user mapping if it points to this session
        if self._user_sessions.get(user_id) == session_id:
            del self._user_sessions[user_id]
        
        logger.info(f"Removed session {session_id} for user {session_data.user_email}")
        
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        async with self._lock:
            expired_sessions = []
            
            for session_id, session_data in self._sessions.items():
                if self._is_session_expired(session_data):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            cleaned_count = 0
            for session_id in expired_sessions:
                if await self._remove_session_internal(session_id):
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
    
    def _is_session_expired(self, session_data: SessionData) -> bool:
        """Check if a session has expired."""
        now = datetime.now(timezone.utc)
        return (now - session_data.last_accessed) > self._session_timeout
    
    async def get_session_count(self) -> int:
        """
        Get total number of active sessions.
        
        Returns:
            Session count
        """
        async with self._lock:
            return len(self._sessions)
    
    async def get_stats(self) -> Dict:
        """
        Get session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            total_sessions = len(self._sessions)
            
            # Calculate session age statistics
            session_ages = []
            for session_data in self._sessions.values():
                age_hours = (now - session_data.created_at).total_seconds() / 3600
                session_ages.append(age_hours)
            
            avg_age = sum(session_ages) / len(session_ages) if session_ages else 0
            
            # Get connection statistics
            connection_stats = await self._connection_manager.get_stats()
            
            return {
                'total_sessions': total_sessions,
                'average_session_age_hours': round(avg_age, 2),
                'session_timeout_hours': self._session_timeout.total_seconds() / 3600,
                'connected_users': connection_stats.get('unique_users', 0),
                'total_connections': connection_stats.get('total_connections', 0)
            }
    
    async def get_all_sessions(self) -> List[SessionData]:
        """
        Get all active sessions.
        
        Returns:
            List of all SessionData objects
        """
        async with self._lock:
            # Filter out expired sessions
            active_sessions = []
            for session_data in self._sessions.values():
                if not self._is_session_expired(session_data):
                    active_sessions.append(session_data)
            
            return active_sessions
    
    async def is_user_session_active(self, user_id: str) -> bool:
        """
        Check if a user has an active session.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active session, False otherwise
        """
        session_data = await self.get_user_session(user_id)
        return session_data is not None
    
    async def get_session_with_connections(self, session_id: str) -> Optional[Dict]:
        """
        Get session data along with connection information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session and connection data, or None
        """
        session_data = await self.get_session(session_id)
        
        if not session_data:
            return None
        
        # Get user connections
        connections = await self._connection_manager.get_user_connections(session_data.user_id)
        
        return {
            'session': session_data.to_dict(),
            'connections': [conn.to_dict() for conn in connections],
            'connection_count': len(connections)
        }


# Global singleton instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Get the global SessionManager instance.
    
    Returns:
        SessionManager singleton
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager