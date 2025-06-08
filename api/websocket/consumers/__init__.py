"""WebSocket consumers for handling real-time connections."""

from .base_consumer import BaseAuthenticatedConsumer, BaseRoomConsumer

__all__ = ['BaseAuthenticatedConsumer', 'BaseRoomConsumer']