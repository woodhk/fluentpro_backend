from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Type, Awaitable
from dataclasses import dataclass
import asyncio
import logging
from domains.shared.events.base_event import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]

class IEventBus(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to the bus"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Subscribe to an event type"""
        pass

class InMemoryEventBus(IEventBus):
    """In-memory event bus for development/testing"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
    
    async def publish(self, event: DomainEvent) -> None:
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event_type}")
            return
        
        # Execute all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any handler errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Handler {handlers[i].__name__} failed: {result}")
    
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        # Create a minimal instance to get the actual event_type value
        try:
            # Try to create instance with minimal required parameters
            if hasattr(event_type, '__annotations__'):
                # Get required fields from annotations
                required_fields = {}
                for field_name, field_type in event_type.__annotations__.items():
                    if field_name in ['user_id', 'aggregate_id']:
                        required_fields[field_name] = "dummy"
                    elif field_name == 'session_id':
                        required_fields[field_name] = "dummy"
                    elif field_name == 'email':
                        required_fields[field_name] = "dummy@example.com"
                    elif field_name in ['full_name', 'auth0_id']:
                        required_fields[field_name] = "dummy"
                    elif field_name in ['total_duration_minutes', 'completion_rate']:
                        required_fields[field_name] = 0
                    elif field_name in ['completed_steps', 'skipped_steps']:
                        required_fields[field_name] = []
                
                dummy_instance = event_type(**required_fields)
                event_type_str = dummy_instance.event_type
            else:
                # Fallback to class name
                event_type_str = event_type.__name__
        except Exception as e:
            # Fallback to class name if instantiation fails
            event_type_str = event_type.__name__
            
        if event_type_str not in self._handlers:
            self._handlers[event_type_str] = []
        self._handlers[event_type_str].append(handler)

class RedisEventBus(IEventBus):
    """Redis-based event bus for production"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._subscriber_task = None
    
    async def start(self):
        """Start listening for events"""
        self._subscriber_task = asyncio.create_task(self._listen_for_events())
    
    async def stop(self):
        """Stop listening for events"""
        if self._subscriber_task:
            self._subscriber_task.cancel()
    
    async def publish(self, event: DomainEvent) -> None:
        # Serialize event
        event_data = event.json()
        
        # Publish to Redis channel
        await self.redis.publish(f"events:{event.event_type}", event_data)
    
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        # Create a minimal instance to get the actual event_type value
        try:
            # Try to create instance with minimal required parameters
            if hasattr(event_type, '__annotations__'):
                # Get required fields from annotations
                required_fields = {}
                for field_name, field_type in event_type.__annotations__.items():
                    if field_name in ['user_id', 'aggregate_id']:
                        required_fields[field_name] = "dummy"
                    elif field_name == 'session_id':
                        required_fields[field_name] = "dummy"
                    elif field_name == 'email':
                        required_fields[field_name] = "dummy@example.com"
                    elif field_name in ['full_name', 'auth0_id']:
                        required_fields[field_name] = "dummy"
                    elif field_name in ['total_duration_minutes', 'completion_rate']:
                        required_fields[field_name] = 0
                    elif field_name in ['completed_steps', 'skipped_steps']:
                        required_fields[field_name] = []
                
                dummy_instance = event_type(**required_fields)
                event_type_str = dummy_instance.event_type
            else:
                # Fallback to class name
                event_type_str = event_type.__name__
        except Exception as e:
            # Fallback to class name if instantiation fails
            event_type_str = event_type.__name__
            
        if event_type_str not in self._handlers:
            self._handlers[event_type_str] = []
        self._handlers[event_type_str].append(handler)
    
    async def _listen_for_events(self):
        """Listen for events from Redis"""
        pubsub = self.redis.pubsub()
        
        # Subscribe to all event channels
        for event_type in self._handlers.keys():
            await pubsub.subscribe(f"events:{event_type}")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                await self._handle_message(message)