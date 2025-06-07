"""Shared events infrastructure for domain events."""

from .base_event import DomainEvent, EventMetadata, EventBus, event_bus
from .publisher import EventPublisher, publishes_event, collect_events
from .registry import EventHandlerRegistry, event_registry, setup_event_handlers, get_event_handlers_summary

__all__ = [
    'DomainEvent',
    'EventMetadata',
    'EventBus',
    'event_bus',
    'EventPublisher',
    'publishes_event',
    'collect_events',
    'EventHandlerRegistry',
    'event_registry',
    'setup_event_handlers',
    'get_event_handlers_summary',
]