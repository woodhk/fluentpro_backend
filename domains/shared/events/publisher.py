"""
Event publishing utilities and decorators.
Provides convenient ways to publish domain events.
"""

import asyncio
from typing import List, Callable, Any
from functools import wraps

from .base_event import DomainEvent, event_bus


class EventPublisher:
    """
    Service for publishing domain events.
    Provides a clean interface for event publishing with error handling.
    """
    
    def __init__(self, bus=None):
        self.bus = bus or event_bus
        self._pending_events = []
    
    async def publish(self, event: DomainEvent):
        """Publish a single event."""
        await self.bus.publish(event)
    
    async def publish_batch(self, events: List[DomainEvent]):
        """Publish multiple events."""
        for event in events:
            await self.publish(event)
    
    def add_pending_event(self, event: DomainEvent):
        """Add an event to be published later."""
        self._pending_events.append(event)
    
    async def publish_pending_events(self):
        """Publish all pending events."""
        if self._pending_events:
            await self.publish_batch(self._pending_events)
            self._pending_events.clear()
    
    def clear_pending_events(self):
        """Clear pending events without publishing."""
        self._pending_events.clear()


def publishes_event(event_class: type):
    """
    Decorator that automatically publishes an event after a method completes.
    
    Usage:
        @publishes_event(UserRegisteredEvent)
        async def register_user(self, user_data):
            # method implementation
            return user  # The returned object should have the data needed for the event
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Create and publish the event
            if hasattr(result, 'id'):
                event = event_class(aggregate_id=result.id, **result.dict())
                publisher = EventPublisher()
                await publisher.publish(event)
            
            return result
        return wrapper
    return decorator


def collect_events(func: Callable) -> Callable:
    """
    Decorator that collects events during method execution and publishes them at the end.
    Useful for transactional operations where you want all events published together.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        publisher = EventPublisher()
        
        # Store original publisher in context if available
        if hasattr(args[0], '_event_publisher'):
            original_publisher = args[0]._event_publisher
            args[0]._event_publisher = publisher
        
        try:
            result = await func(*args, **kwargs)
            # Publish all collected events
            await publisher.publish_pending_events()
            return result
        except Exception:
            # Clear events on error
            publisher.clear_pending_events()
            raise
        finally:
            # Restore original publisher
            if hasattr(args[0], '_event_publisher'):
                args[0]._event_publisher = original_publisher
    
    return wrapper