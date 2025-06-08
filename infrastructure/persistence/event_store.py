"""
Event store implementation for persisting and retrieving domain events.
Provides interface and implementation for event sourcing capabilities.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from domains.shared.events.base_event import DomainEvent
from infrastructure.persistence.supabase.client import get_supabase_client


logger = logging.getLogger(__name__)


class IEventStore(ABC):
    """Interface for event store operations."""
    
    @abstractmethod
    async def save_events(self, aggregate_id: str, events: List[DomainEvent], expected_version: int) -> None:
        """
        Save events for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            events: List of events to save
            expected_version: Expected version for optimistic concurrency control
            
        Raises:
            ConcurrencyException: If expected version doesn't match actual version
        """
        pass
    
    @abstractmethod
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """
        Get all events for an aggregate from a specific version.
        
        Args:
            aggregate_id: ID of the aggregate
            from_version: Starting version (default: 0 for all events)
            
        Returns:
            List of domain events ordered by version
        """
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self, 
        event_type: str, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """
        Get events by type within a date range.
        
        Args:
            event_type: Type of events to retrieve
            from_date: Start date (optional)
            to_date: End date (optional)
            
        Returns:
            List of domain events matching criteria
        """
        pass
    
    @abstractmethod
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """
        Get the current version of an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            Current version number (0 if aggregate doesn't exist)
        """
        pass
    
    @abstractmethod
    async def get_events_stream(
        self, 
        from_position: int = 0, 
        batch_size: int = 100
    ) -> List[DomainEvent]:
        """
        Get events from the global event stream.
        
        Args:
            from_position: Starting position in the stream
            batch_size: Maximum number of events to return
            
        Returns:
            List of domain events ordered by position
        """
        pass


class ConcurrencyException(Exception):
    """Exception raised when optimistic concurrency control fails."""
    
    def __init__(self, aggregate_id: str, expected_version: int, actual_version: int):
        self.aggregate_id = aggregate_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Concurrency conflict for aggregate {aggregate_id}. "
            f"Expected version {expected_version}, but actual version is {actual_version}"
        )


class SupabaseEventStore(IEventStore):
    """Event store implementation using Supabase."""
    
    def __init__(self):
        self._client = None
    
    async def _get_client(self):
        """Get Supabase client instance."""
        if self._client is None:
            self._client = await get_supabase_client()
        return self._client
    
    async def save_events(self, aggregate_id: str, events: List[DomainEvent], expected_version: int) -> None:
        """Save events for an aggregate with optimistic concurrency control."""
        if not events:
            return
        
        client = await self._get_client()
        
        try:
            # Check current version for optimistic concurrency control
            current_version = await self.get_aggregate_version(aggregate_id)
            
            if current_version != expected_version:
                raise ConcurrencyException(aggregate_id, expected_version, current_version)
            
            # Prepare event records for insertion
            event_records = []
            for i, event in enumerate(events):
                version = expected_version + i + 1
                event_record = {
                    'aggregate_id': aggregate_id,
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'event_version': version,
                    'event_data': event.dict(),
                    'occurred_at': event.occurred_at.isoformat(),
                    'correlation_id': event.correlation_id,
                    'causation_id': event.causation_id,
                    'metadata': json.dumps(event.metadata)
                }
                event_records.append(event_record)
            
            # Insert events in a transaction
            result = client.table('event_store').insert(event_records).execute()
            
            if not result.data:
                raise Exception("Failed to save events")
            
            logger.info(f"Saved {len(events)} events for aggregate {aggregate_id}")
            
        except ConcurrencyException:
            raise
        except Exception as e:
            logger.error(f"Error saving events for aggregate {aggregate_id}: {e}")
            raise
    
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Get all events for an aggregate from a specific version."""
        client = await self._get_client()
        
        try:
            query = (
                client.table('event_store')
                .select('*')
                .eq('aggregate_id', aggregate_id)
                .gte('event_version', from_version)
                .order('event_version')
            )
            
            result = query.execute()
            
            if not result.data:
                return []
            
            events = []
            for record in result.data:
                event_data = record['event_data']
                
                # Reconstruct the domain event
                # Note: In a real implementation, you'd have a registry of event types
                # and deserialize to the correct concrete event class
                event = self._deserialize_event(event_data)
                events.append(event)
            
            logger.info(f"Retrieved {len(events)} events for aggregate {aggregate_id}")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving events for aggregate {aggregate_id}: {e}")
            raise
    
    async def get_events_by_type(
        self, 
        event_type: str, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Get events by type within a date range."""
        client = await self._get_client()
        
        try:
            query = (
                client.table('event_store')
                .select('*')
                .eq('event_type', event_type)
                .order('occurred_at')
            )
            
            if from_date:
                query = query.gte('occurred_at', from_date.isoformat())
            
            if to_date:
                query = query.lte('occurred_at', to_date.isoformat())
            
            result = query.execute()
            
            if not result.data:
                return []
            
            events = []
            for record in result.data:
                event_data = record['event_data']
                event = self._deserialize_event(event_data)
                events.append(event)
            
            logger.info(f"Retrieved {len(events)} events of type {event_type}")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving events by type {event_type}: {e}")
            raise
    
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """Get the current version of an aggregate."""
        client = await self._get_client()
        
        try:
            result = (
                client.table('event_store')
                .select('event_version')
                .eq('aggregate_id', aggregate_id)
                .order('event_version', desc=True)
                .limit(1)
                .execute()
            )
            
            if not result.data:
                return 0
            
            return result.data[0]['event_version']
            
        except Exception as e:
            logger.error(f"Error getting version for aggregate {aggregate_id}: {e}")
            raise
    
    async def get_events_stream(
        self, 
        from_position: int = 0, 
        batch_size: int = 100
    ) -> List[DomainEvent]:
        """Get events from the global event stream."""
        client = await self._get_client()
        
        try:
            result = (
                client.table('event_store')
                .select('*')
                .gte('id', from_position)
                .order('id')
                .limit(batch_size)
                .execute()
            )
            
            if not result.data:
                return []
            
            events = []
            for record in result.data:
                event_data = record['event_data']
                event = self._deserialize_event(event_data)
                events.append(event)
            
            logger.info(f"Retrieved {len(events)} events from stream starting at position {from_position}")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving events from stream: {e}")
            raise
    
    def _deserialize_event(self, event_data: Dict[str, Any]) -> DomainEvent:
        """
        Deserialize event data to a DomainEvent instance.
        
        Note: In a production system, you would have a registry of event types
        and deserialize to the correct concrete event class based on event_type.
        For now, we create a generic DomainEvent.
        """
        # Parse datetime fields
        if 'occurred_at' in event_data and isinstance(event_data['occurred_at'], str):
            event_data['occurred_at'] = datetime.fromisoformat(event_data['occurred_at'].replace('Z', '+00:00'))
        
        # Create a basic DomainEvent
        # In production, you'd use an event registry to get the correct type
        event = DomainEvent(**event_data)
        return event


class InMemoryEventStore(IEventStore):
    """In-memory event store implementation for testing."""
    
    def __init__(self):
        self._events: Dict[str, List[DomainEvent]] = {}
        self._global_position = 0
    
    async def save_events(self, aggregate_id: str, events: List[DomainEvent], expected_version: int) -> None:
        """Save events for an aggregate."""
        if not events:
            return
        
        current_version = await self.get_aggregate_version(aggregate_id)
        
        if current_version != expected_version:
            raise ConcurrencyException(aggregate_id, expected_version, current_version)
        
        if aggregate_id not in self._events:
            self._events[aggregate_id] = []
        
        for event in events:
            self._events[aggregate_id].append(event)
        
        logger.info(f"Saved {len(events)} events for aggregate {aggregate_id}")
    
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Get all events for an aggregate from a specific version."""
        if aggregate_id not in self._events:
            return []
        
        # Filter events by version (assuming events are stored in order)
        events = self._events[aggregate_id]
        if from_version > 0:
            events = events[from_version:]
        
        return events.copy()
    
    async def get_events_by_type(
        self, 
        event_type: str, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Get events by type within a date range."""
        matching_events = []
        
        for aggregate_events in self._events.values():
            for event in aggregate_events:
                if event.event_type == event_type:
                    # Check date range if specified
                    if from_date and event.occurred_at < from_date:
                        continue
                    if to_date and event.occurred_at > to_date:
                        continue
                    
                    matching_events.append(event)
        
        # Sort by occurrence time
        matching_events.sort(key=lambda e: e.occurred_at)
        return matching_events
    
    async def get_aggregate_version(self, aggregate_id: str) -> int:
        """Get the current version of an aggregate."""
        if aggregate_id not in self._events:
            return 0
        
        return len(self._events[aggregate_id])
    
    async def get_events_stream(
        self, 
        from_position: int = 0, 
        batch_size: int = 100
    ) -> List[DomainEvent]:
        """Get events from the global event stream."""
        all_events = []
        
        for aggregate_events in self._events.values():
            all_events.extend(aggregate_events)
        
        # Sort by occurrence time
        all_events.sort(key=lambda e: e.occurred_at)
        
        # Apply pagination
        start = from_position
        end = start + batch_size
        return all_events[start:end]


# Factory function for getting event store instance
_event_store_instance: Optional[IEventStore] = None


async def get_event_store() -> IEventStore:
    """Get the configured event store instance."""
    global _event_store_instance
    
    if _event_store_instance is None:
        # In production, this would be configured via settings
        # For now, default to Supabase implementation
        _event_store_instance = SupabaseEventStore()
    
    return _event_store_instance


def set_event_store(event_store: IEventStore) -> None:
    """Set the event store instance (mainly for testing)."""
    global _event_store_instance
    _event_store_instance = event_store