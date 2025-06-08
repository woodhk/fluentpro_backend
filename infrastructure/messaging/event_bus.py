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
    
    async def _handle_message(self, message):
        """Handle incoming Redis message"""
        try:
            # Extract event type from channel name
            channel = message['channel'].decode('utf-8')
            event_type = channel.replace('events:', '')
            
            # Get registered handlers
            handlers = self._handlers.get(event_type, [])
            if not handlers:
                logger.warning(f"No handlers registered for event type: {event_type}")
                return
            
            # Deserialize event data
            event_data = message['data'].decode('utf-8')
            # Note: Would need proper event deserialization based on event type
            
            # Execute handlers (simplified for now)
            for handler in handlers:
                try:
                    # Would need to reconstruct actual event object here
                    # await handler(reconstructed_event)
                    pass
                except Exception as e:
                    logger.error(f"Handler failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to handle Redis message: {e}")


class RedisStreamsEventBus(IEventBus):
    """Redis Streams-based event bus with consumer groups and acknowledgments"""
    
    def __init__(
        self,
        redis_streams_client,
        consumer_group: str = "default",
        consumer_name: str = "worker-1",
        stream_prefix: str = "events:"
    ):
        """
        Initialize Redis Streams event bus
        
        Args:
            redis_streams_client: RedisStreamsClient instance
            consumer_group: Name of the consumer group
            consumer_name: Name of this consumer
            stream_prefix: Prefix for event stream names
        """
        from ..persistence.cache.redis_client import RedisStreamsClient
        
        if not isinstance(redis_streams_client, RedisStreamsClient):
            raise ValueError("redis_streams_client must be an instance of RedisStreamsClient")
            
        self.streams_client = redis_streams_client
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.stream_prefix = stream_prefix
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._consumer_task = None
        self._running = False
    
    async def start(self) -> None:
        """Start the event bus consumer"""
        if self._running:
            logger.warning("Event bus is already running")
            return
        
        try:
            # Ensure Redis connection
            if not self.streams_client.is_connected:
                await self.streams_client.connect()
            
            # Create consumer groups for all registered event types
            for event_type in self._handlers.keys():
                stream_name = f"{self.stream_prefix}{event_type}"
                await self.streams_client.create_consumer_group(
                    stream_name, 
                    self.consumer_group,
                    start_id="0"  # Start from beginning for reliability
                )
            
            self._running = True
            self._consumer_task = asyncio.create_task(self._consume_events())
            logger.info(f"Redis Streams event bus started (group: {self.consumer_group}, consumer: {self.consumer_name})")
            
        except Exception as e:
            logger.error(f"Failed to start Redis Streams event bus: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the event bus consumer"""
        if not self._running:
            return
        
        self._running = False
        
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Redis Streams event bus stopped")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to Redis Stream
        
        Args:
            event: Domain event to publish
        """
        try:
            stream_name = f"{self.stream_prefix}{event.event_type}"
            
            # Prepare event data
            event_data = {
                "event_type": event.event_type,
                "event_data": event.json(),
                "published_at": event.occurred_at.isoformat() if hasattr(event, 'occurred_at') else None,
                "published_by": self.consumer_name
            }
            
            # Add to stream
            message_id = await self.streams_client.add_to_stream(
                stream_name, 
                event_data,
                maxlen=10000  # Keep last 10k messages per stream
            )
            
            logger.debug(f"Published event {event.event_type} to stream {stream_name} with ID {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise
    
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of domain event to subscribe to
            handler: Async handler function for the event
        """
        # Get event type string using the same logic as other buses
        try:
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
        logger.info(f"Subscribed to event type: {event_type_str}")
    
    async def _consume_events(self) -> None:
        """Main consumer loop for processing events"""
        logger.info("Starting event consumption loop")
        
        while self._running:
            try:
                # Process events for each registered event type
                for event_type in self._handlers.keys():
                    await self._process_stream_events(event_type)
                
                # Check for and claim pending messages from other consumers
                await self._claim_pending_messages()
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                logger.info("Event consumption cancelled")
                break
            except Exception as e:
                logger.error(f"Error in event consumption loop: {e}")
                await asyncio.sleep(1)  # Back off on error
    
    async def _process_stream_events(self, event_type: str) -> None:
        """Process events from a specific stream"""
        try:
            stream_name = f"{self.stream_prefix}{event_type}"
            
            # Read new messages from stream
            messages = await self.streams_client.read_from_stream(
                stream_name,
                self.consumer_group,
                self.consumer_name,
                count=10,  # Process up to 10 messages at a time
                block_ms=100  # Short block time for responsiveness
            )
            
            for message in messages:
                await self._handle_stream_message(message, event_type)
                
        except Exception as e:
            logger.error(f"Failed to process events from stream {event_type}: {e}")
    
    async def _handle_stream_message(self, message, event_type: str) -> None:
        """Handle a single stream message"""
        try:
            # Get handlers for this event type
            handlers = self._handlers.get(event_type, [])
            if not handlers:
                logger.warning(f"No handlers for event type: {event_type}")
                # Still acknowledge the message
                await self.streams_client.acknowledge_message(
                    message.stream_name,
                    self.consumer_group,
                    message.message_id
                )
                return
            
            # Reconstruct the domain event
            event_data_str = message.data.get("event_data", "{}")
            
            # Execute all handlers
            handler_results = []
            for handler in handlers:
                try:
                    # Note: In a real implementation, you'd need to deserialize
                    # the event back to its proper domain event class
                    # For now, we'll pass the raw data
                    await handler(message.data)
                    handler_results.append(True)
                except Exception as e:
                    logger.error(f"Handler failed for message {message.message_id}: {e}")
                    handler_results.append(False)
            
            # Only acknowledge if all handlers succeeded
            if all(handler_results):
                await self.streams_client.acknowledge_message(
                    message.stream_name,
                    self.consumer_group,
                    message.message_id
                )
                logger.debug(f"Successfully processed and acknowledged message {message.message_id}")
            else:
                logger.error(f"Not acknowledging message {message.message_id} due to handler failures")
                
        except Exception as e:
            logger.error(f"Failed to handle stream message {message.message_id}: {e}")
    
    async def _claim_pending_messages(self) -> None:
        """Claim and process pending messages from failed consumers"""
        try:
            for event_type in self._handlers.keys():
                stream_name = f"{self.stream_prefix}{event_type}"
                
                # Claim messages that have been pending for more than 1 minute
                claimed_messages = await self.streams_client.claim_pending_messages(
                    stream_name,
                    self.consumer_group,
                    self.consumer_name,
                    min_idle_time_ms=60000  # 1 minute
                )
                
                if claimed_messages:
                    logger.info(f"Claimed {len(claimed_messages)} pending messages from stream {stream_name}")
                    
                    for message in claimed_messages:
                        await self._handle_stream_message(message, event_type)
                        
        except Exception as e:
            logger.error(f"Failed to claim pending messages: {e}")
    
    async def get_consumer_info(self) -> Dict[str, Any]:
        """Get information about this consumer"""
        info = {
            "consumer_group": self.consumer_group,
            "consumer_name": self.consumer_name,
            "stream_prefix": self.stream_prefix,
            "registered_event_types": list(self._handlers.keys()),
            "running": self._running,
            "connected": self.streams_client.is_connected
        }
        
        return info
    
    async def get_stream_stats(self) -> Dict[str, Any]:
        """Get statistics for all registered streams"""
        stats = {}
        
        try:
            for event_type in self._handlers.keys():
                stream_name = f"{self.stream_prefix}{event_type}"
                try:
                    stream_info = await self.streams_client.get_stream_info(stream_name)
                    stats[event_type] = {
                        "stream_name": stream_name,
                        "length": stream_info.get("length", 0),
                        "groups": stream_info.get("groups", 0),
                        "last_entry_id": stream_info.get("last-entry", [None])[0]
                    }
                except Exception as e:
                    stats[event_type] = {"error": str(e)}
                    
        except Exception as e:
            logger.error(f"Failed to get stream stats: {e}")
            
        return stats