"""
Base domain event class and related infrastructure.
Provides the foundation for all domain events in the system.
"""

import uuid
from datetime import datetime
from abc import ABC
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DomainEvent(BaseModel, ABC):
    """
    Base class for all domain events.
    
    Domain events represent something significant that happened in the domain
    that domain experts care about.
    """
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    aggregate_id: str = Field(..., description="ID of the aggregate that produced this event")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="When the event occurred")
    event_type: str = Field(..., description="Type of the event")
    event_version: int = Field(default=1, description="Version of the event schema")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking related events")
    causation_id: Optional[str] = Field(None, description="ID of the event that caused this event")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "aggregate_id": "user-456",
                "occurred_at": "2024-01-15T10:30:00Z",
                "event_type": "user.registered",
                "event_version": 1,
                "correlation_id": "correlation-123",
                "causation_id": "causation-456",
                "metadata": {
                    "source": "web_api",
                    "user_agent": "Mozilla/5.0..."
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return self.dict()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the event."""
        self.metadata[key] = value
    
    def with_correlation_id(self, correlation_id: str) -> 'DomainEvent':
        """Create a copy of the event with a correlation ID."""
        event_copy = self.copy()
        event_copy.correlation_id = correlation_id
        return event_copy
    
    def with_causation_id(self, causation_id: str) -> 'DomainEvent':
        """Create a copy of the event with a causation ID."""
        event_copy = self.copy()
        event_copy.causation_id = causation_id
        return event_copy


class EventMetadata:
    """Helper class for common event metadata."""
    
    @staticmethod
    def from_request(request_id: str, user_id: Optional[str] = None, source: str = "api") -> Dict[str, Any]:
        """Create metadata from a request context."""
        metadata = {
            "request_id": request_id,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            metadata["user_id"] = user_id
            
        return metadata
    
    @staticmethod
    def from_system(component: str, action: str) -> Dict[str, Any]:
        """Create metadata for system-generated events."""
        return {
            "source": "system",
            "component": component,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }


class EventBus:
    """
    Simple event bus interface for publishing domain events.
    This is a basic implementation - in production you might use a message queue.
    """
    
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: str, handler):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: DomainEvent):
        """Publish an event to all registered handlers."""
        handlers = self._handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # In production, you'd want proper error handling and retry logic
                print(f"Error handling event {event.event_type}: {e}")
    
    def get_handlers(self, event_type: str):
        """Get all handlers for a specific event type."""
        return self._handlers.get(event_type, [])


# Global event bus instance
event_bus = EventBus()