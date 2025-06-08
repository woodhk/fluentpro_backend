"""
Event sourcing pattern implementation.
Provides base classes and utilities for event-sourced aggregates.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Optional
from datetime import datetime

from domains.shared.events.base_event import DomainEvent
from domains.shared.models.base_entity import BaseEntity
from infrastructure.persistence.event_store import get_event_store, ConcurrencyException


logger = logging.getLogger(__name__)


class EventSourcedAggregate(BaseEntity, ABC):
    """
    Base class for event-sourced aggregates.
    
    Extends BaseEntity to provide event sourcing capabilities including:
    - Loading aggregate state from events
    - Applying events to rebuild state
    - Tracking uncommitted events
    - Optimistic concurrency control
    """
    
    def __init__(self, aggregate_id: str):
        super().__init__()
        self._aggregate_id = aggregate_id
        self._version = 0
        self._uncommitted_events: List[DomainEvent] = []
        self._is_replaying = False
    
    @property
    def aggregate_id(self) -> str:
        """Get the aggregate ID."""
        return self._aggregate_id
    
    @property
    def version(self) -> int:
        """Get the current version of the aggregate."""
        return self._version
    
    @property
    def uncommitted_events(self) -> List[DomainEvent]:
        """Get list of uncommitted events."""
        return self._uncommitted_events.copy()
    
    @property
    def has_uncommitted_events(self) -> bool:
        """Check if there are uncommitted events."""
        return len(self._uncommitted_events) > 0
    
    def mark_events_as_committed(self) -> None:
        """Mark all uncommitted events as committed."""
        self._uncommitted_events.clear()
    
    def apply_event(self, event: DomainEvent) -> None:
        """
        Apply an event to the aggregate.
        
        This method handles both new events (when sourcing) and historical events
        (when replaying from event store).
        
        Args:
            event: The domain event to apply
        """
        # Apply the event to update aggregate state
        self._apply_event_to_state(event)
        
        # Increment version
        self._version += 1
        
        # If not replaying, track as uncommitted event
        if not self._is_replaying:
            self._uncommitted_events.append(event)
            # Also add to domain events for immediate publication if needed
            self.add_domain_event(event)
    
    @abstractmethod
    def _apply_event_to_state(self, event: DomainEvent) -> None:
        """
        Apply an event to the aggregate's internal state.
        
        This method must be implemented by concrete aggregates to handle
        their specific event types and state changes.
        
        Args:
            event: The domain event to apply to state
        """
        pass
    
    async def load_from_history(self, events: List[DomainEvent]) -> None:
        """
        Load aggregate state from a list of historical events.
        
        Args:
            events: List of events to replay in order
        """
        self._is_replaying = True
        try:
            for event in events:
                self.apply_event(event)
        finally:
            self._is_replaying = False
        
        # Clear uncommitted events after replay
        self._uncommitted_events.clear()
        logger.info(f"Loaded aggregate {self._aggregate_id} from {len(events)} events, version: {self._version}")
    
    async def save_to_event_store(self) -> None:
        """
        Save uncommitted events to the event store.
        
        Raises:
            ConcurrencyException: If there's a concurrency conflict
        """
        if not self.has_uncommitted_events:
            return
        
        event_store = await get_event_store()
        
        try:
            # Calculate expected version (current version - uncommitted events)
            expected_version = self._version - len(self._uncommitted_events)
            
            await event_store.save_events(
                self._aggregate_id,
                self._uncommitted_events,
                expected_version
            )
            
            # Mark events as committed
            self.mark_events_as_committed()
            
            logger.info(f"Saved {len(self._uncommitted_events)} events for aggregate {self._aggregate_id}")
            
        except ConcurrencyException as e:
            logger.error(f"Concurrency conflict saving aggregate {self._aggregate_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving aggregate {self._aggregate_id}: {e}")
            raise


class AggregateRepository(ABC):
    """
    Base repository class for event-sourced aggregates.
    
    Provides common functionality for loading and saving event-sourced aggregates.
    """
    
    def __init__(self):
        self._event_store = None
    
    async def _get_event_store(self):
        """Get event store instance."""
        if self._event_store is None:
            self._event_store = await get_event_store()
        return self._event_store
    
    @abstractmethod
    def _create_aggregate(self, aggregate_id: str) -> EventSourcedAggregate:
        """
        Create a new instance of the aggregate.
        
        Args:
            aggregate_id: ID for the new aggregate
            
        Returns:
            New aggregate instance
        """
        pass
    
    async def get_by_id(self, aggregate_id: str) -> Optional[EventSourcedAggregate]:
        """
        Load an aggregate by ID from the event store.
        
        Args:
            aggregate_id: ID of the aggregate to load
            
        Returns:
            The aggregate instance or None if not found
        """
        event_store = await self._get_event_store()
        
        try:
            # Get all events for the aggregate
            events = await event_store.get_events(aggregate_id)
            
            if not events:
                return None
            
            # Create new aggregate instance
            aggregate = self._create_aggregate(aggregate_id)
            
            # Load from events
            await aggregate.load_from_history(events)
            
            return aggregate
            
        except Exception as e:
            logger.error(f"Error loading aggregate {aggregate_id}: {e}")
            raise
    
    async def save(self, aggregate: EventSourcedAggregate) -> None:
        """
        Save an aggregate to the event store.
        
        Args:
            aggregate: The aggregate to save
            
        Raises:
            ConcurrencyException: If there's a concurrency conflict
        """
        try:
            await aggregate.save_to_event_store()
            logger.info(f"Saved aggregate {aggregate.aggregate_id}")
            
        except ConcurrencyException as e:
            logger.error(f"Concurrency conflict saving aggregate {aggregate.aggregate_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving aggregate {aggregate.aggregate_id}: {e}")
            raise
    
    async def exists(self, aggregate_id: str) -> bool:
        """
        Check if an aggregate exists.
        
        Args:
            aggregate_id: ID of the aggregate to check
            
        Returns:
            True if aggregate exists, False otherwise
        """
        event_store = await self._get_event_store()
        
        try:
            version = await event_store.get_aggregate_version(aggregate_id)
            return version > 0
            
        except Exception as e:
            logger.error(f"Error checking existence of aggregate {aggregate_id}: {e}")
            raise


class EventSourcedAggregateBuilder:
    """
    Builder for creating event-sourced aggregates with specific configurations.
    """
    
    def __init__(self, aggregate_class: Type[EventSourcedAggregate]):
        self._aggregate_class = aggregate_class
        self._aggregate_id: Optional[str] = None
        self._events: List[DomainEvent] = []
    
    def with_id(self, aggregate_id: str) -> 'EventSourcedAggregateBuilder':
        """Set the aggregate ID."""
        self._aggregate_id = aggregate_id
        return self
    
    def with_events(self, events: List[DomainEvent]) -> 'EventSourcedAggregateBuilder':
        """Set the events to replay."""
        self._events = events
        return self
    
    async def build(self) -> EventSourcedAggregate:
        """
        Build the aggregate instance.
        
        Returns:
            Configured aggregate instance
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not self._aggregate_id:
            raise ValueError("Aggregate ID is required")
        
        # Create aggregate instance
        aggregate = self._aggregate_class(self._aggregate_id)
        
        # Load from events if provided
        if self._events:
            await aggregate.load_from_history(self._events)
        
        return aggregate


class Snapshot:
    """
    Represents a snapshot of aggregate state at a specific version.
    
    Snapshots can be used to optimize aggregate loading by avoiding
    replaying all events from the beginning.
    """
    
    def __init__(
        self, 
        aggregate_id: str, 
        aggregate_type: str, 
        version: int, 
        data: Dict[str, Any], 
        timestamp: datetime = None
    ):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = version
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'version': self.version,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """Create snapshot from dictionary."""
        timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        return cls(
            aggregate_id=data['aggregate_id'],
            aggregate_type=data['aggregate_type'],
            version=data['version'],
            data=data['data'],
            timestamp=timestamp
        )


class SnapshotableAggregate(EventSourcedAggregate, ABC):
    """
    Event-sourced aggregate that supports snapshotting.
    
    Extends EventSourcedAggregate to provide snapshot capabilities
    for performance optimization.
    """
    
    @abstractmethod
    def take_snapshot(self) -> Snapshot:
        """
        Take a snapshot of the current aggregate state.
        
        Returns:
            Snapshot instance representing current state
        """
        pass
    
    @abstractmethod
    async def load_from_snapshot(self, snapshot: Snapshot) -> None:
        """
        Load aggregate state from a snapshot.
        
        Args:
            snapshot: The snapshot to load from
        """
        pass
    
    async def load_from_snapshot_and_events(
        self, 
        snapshot: Snapshot, 
        events_since_snapshot: List[DomainEvent]
    ) -> None:
        """
        Load aggregate from snapshot and apply subsequent events.
        
        Args:
            snapshot: The snapshot to start from
            events_since_snapshot: Events that occurred after the snapshot
        """
        # Load from snapshot
        await self.load_from_snapshot(snapshot)
        
        # Set version to snapshot version
        self._version = snapshot.version
        
        # Apply events since snapshot
        if events_since_snapshot:
            await self.load_from_history(events_since_snapshot)
        
        logger.info(
            f"Loaded aggregate {self._aggregate_id} from snapshot (v{snapshot.version}) "
            f"+ {len(events_since_snapshot)} events, final version: {self._version}"
        )