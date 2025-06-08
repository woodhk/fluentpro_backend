"""
Server-Sent Events (SSE) support for real-time HTTP streaming.

This module provides SSE response classes and view mixins for implementing
real-time updates to browser clients without WebSockets.
"""

import json
import asyncio
import uuid
import time
import logging
from typing import Dict, Any, Optional, AsyncIterator, Iterator, Callable, List, Union
from datetime import datetime
from django.http import StreamingHttpResponse, HttpRequest, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class SSEEvent:
    """
    Represents a single Server-Sent Event.
    
    Encapsulates the data, event type, ID, and retry information
    for a single SSE event according to the W3C specification.
    """
    
    def __init__(
        self,
        data: Any,
        event_type: Optional[str] = None,
        event_id: Optional[str] = None,
        retry: Optional[int] = None,
        comment: Optional[str] = None
    ):
        """
        Initialize SSE event.
        
        Args:
            data: Event data (will be JSON-encoded if not string)
            event_type: Optional event type for client-side filtering
            event_id: Unique event ID for client-side tracking
            retry: Reconnection timeout in milliseconds
            comment: Optional comment (ignored by clients)
        """
        self.data = data
        self.event_type = event_type
        self.event_id = event_id or str(uuid.uuid4())
        self.retry = retry
        self.comment = comment
        self.timestamp = datetime.utcnow()
    
    def format(self) -> str:
        """
        Format event according to SSE specification.
        
        Returns:
            Properly formatted SSE event string
        """
        lines = []
        
        # Add comment if provided
        if self.comment:
            lines.append(f": {self.comment}")
        
        # Add event type
        if self.event_type:
            lines.append(f"event: {self.event_type}")
        
        # Add event ID
        lines.append(f"id: {self.event_id}")
        
        # Add retry timeout
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Add data (can be multi-line)
        if isinstance(self.data, str):
            data_str = self.data
        else:
            data_str = json.dumps(self.data, cls=DjangoJSONEncoder)
        
        # Handle multi-line data
        for line in data_str.split('\n'):
            lines.append(f"data: {line}")
        
        # End with double newline
        lines.append("")
        lines.append("")
        
        return '\n'.join(lines)


class SSEConnectionManager:
    """
    Manages active SSE connections and provides broadcasting capabilities.
    
    Tracks client connections, handles disconnections, and provides
    utilities for broadcasting events to multiple clients.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.event_history: List[SSEEvent] = []
        self.max_history_size = 100
    
    def add_connection(
        self, 
        connection_id: str, 
        request: HttpRequest,
        last_event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new SSE connection.
        
        Args:
            connection_id: Unique connection identifier
            request: HTTP request object
            last_event_id: Last event ID received by client (for reconnection)
            
        Returns:
            Connection info dictionary
        """
        connection_info = {
            "id": connection_id,
            "connected_at": datetime.utcnow(),
            "last_event_id": last_event_id,
            "user_agent": request.META.get('HTTP_USER_AGENT', ''),
            "remote_addr": request.META.get('REMOTE_ADDR', ''),
            "is_active": True
        }
        
        self.connections[connection_id] = connection_info
        logger.info(f"SSE connection added: {connection_id}")
        
        return connection_info
    
    def remove_connection(self, connection_id: str):
        """Remove SSE connection."""
        if connection_id in self.connections:
            self.connections[connection_id]["is_active"] = False
            del self.connections[connection_id]
            logger.info(f"SSE connection removed: {connection_id}")
    
    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection info by ID."""
        return self.connections.get(connection_id)
    
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get list of all active connections."""
        return [conn for conn in self.connections.values() if conn["is_active"]]
    
    def add_event_to_history(self, event: SSEEvent):
        """Add event to history for client reconnections."""
        self.event_history.append(event)
        
        # Maintain history size limit
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def get_events_since(self, event_id: str) -> List[SSEEvent]:
        """Get events since specific event ID for reconnection."""
        if not event_id:
            return []
        
        events_since = []
        found_event = False
        
        for event in self.event_history:
            if found_event:
                events_since.append(event)
            elif event.event_id == event_id:
                found_event = True
        
        return events_since


class SSEResponse(StreamingHttpResponse):
    """
    Server-Sent Events HTTP response.
    
    Provides properly formatted SSE responses with correct headers
    and event streaming capabilities.
    """
    
    def __init__(
        self,
        streaming_content: Union[Iterator[SSEEvent], AsyncIterator[SSEEvent]],
        connection_id: Optional[str] = None,
        retry_timeout: int = 3000,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize SSE response.
        
        Args:
            streaming_content: Iterator yielding SSEEvent objects
            connection_id: Optional connection ID for tracking
            retry_timeout: Default retry timeout in milliseconds
            headers: Additional headers to include
        """
        self.connection_id = connection_id or str(uuid.uuid4())
        self.retry_timeout = retry_timeout
        
        # Convert SSEEvent iterator to string iterator
        if hasattr(streaming_content, '__aiter__'):
            content_iterator = self._async_event_iterator(streaming_content)
        else:
            content_iterator = self._sync_event_iterator(streaming_content)
        
        super().__init__(
            streaming_content=content_iterator,
            content_type='text/event-stream',
            headers=headers
        )
        
        # Set required SSE headers
        self['Cache-Control'] = 'no-cache'
        self['Connection'] = 'keep-alive'
        self['Access-Control-Allow-Origin'] = '*'
        self['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        # Add custom headers
        if headers:
            for key, value in headers.items():
                self[key] = value
    
    def _sync_event_iterator(self, event_iterator: Iterator[SSEEvent]) -> Iterator[str]:
        """Convert sync SSEEvent iterator to string iterator."""
        for event in event_iterator:
            yield event.format()
    
    def _async_event_iterator(self, event_iterator: AsyncIterator[SSEEvent]) -> Iterator[str]:
        """Convert async SSEEvent iterator to sync string iterator."""
        async def _async_generator():
            async for event in event_iterator:
                yield event.format()
        
        # Convert async iterator to sync for Django compatibility
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async_gen = _async_generator()
        
        def sync_generator():
            try:
                while True:
                    try:
                        yield loop.run_until_complete(async_gen.__anext__())
                    except StopAsyncIteration:
                        break
            finally:
                loop.run_until_complete(async_gen.aclose())
        
        return sync_generator()


class SSEViewMixin:
    """
    Mixin for adding SSE capabilities to Django views.
    
    Provides utility methods for creating SSE responses,
    managing connections, and handling SSE-specific logic.
    """
    
    sse_connection_manager = SSEConnectionManager()
    
    def get_sse_headers(self) -> Dict[str, str]:
        """Get default SSE headers. Override in subclasses if needed."""
        return {
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control, Last-Event-ID'
        }
    
    def get_last_event_id(self, request: HttpRequest) -> Optional[str]:
        """Extract Last-Event-ID from request headers."""
        return request.META.get('HTTP_LAST_EVENT_ID')
    
    def create_sse_event(
        self,
        data: Any,
        event_type: Optional[str] = None,
        event_id: Optional[str] = None,
        retry: Optional[int] = None
    ) -> SSEEvent:
        """Create SSE event with optional parameters."""
        return SSEEvent(
            data=data,
            event_type=event_type,
            event_id=event_id,
            retry=retry
        )
    
    def create_sse_response(
        self,
        event_generator: Union[Iterator[SSEEvent], AsyncIterator[SSEEvent]],
        request: HttpRequest,
        retry_timeout: int = 3000
    ) -> SSEResponse:
        """
        Create SSE response with connection management.
        
        Args:
            event_generator: Iterator yielding SSEEvent objects
            request: HTTP request object
            retry_timeout: Retry timeout in milliseconds
            
        Returns:
            SSEResponse object ready to return from view
        """
        connection_id = str(uuid.uuid4())
        last_event_id = self.get_last_event_id(request)
        
        # Register connection
        self.sse_connection_manager.add_connection(
            connection_id=connection_id,
            request=request,
            last_event_id=last_event_id
        )
        
        # If client is reconnecting, send missed events first
        if last_event_id:
            missed_events = self.sse_connection_manager.get_events_since(last_event_id)
            if missed_events:
                # Prepend missed events to the generator
                event_generator = self._prepend_events(missed_events, event_generator)
        
        response = SSEResponse(
            streaming_content=event_generator,
            connection_id=connection_id,
            retry_timeout=retry_timeout,
            headers=self.get_sse_headers()
        )
        
        return response
    
    def _prepend_events(
        self, 
        missed_events: List[SSEEvent], 
        event_generator: Union[Iterator[SSEEvent], AsyncIterator[SSEEvent]]
    ) -> Iterator[SSEEvent]:
        """Prepend missed events to event generator."""
        # Yield missed events first
        for event in missed_events:
            yield event
        
        # Then yield from the main generator
        if hasattr(event_generator, '__aiter__'):
            # Handle async generator
            async def async_wrapper():
                async for event in event_generator:
                    yield event
            
            # Convert to sync iterator
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async_gen = async_wrapper()
            
            def sync_wrapper():
                try:
                    while True:
                        try:
                            yield loop.run_until_complete(async_gen.__anext__())
                        except StopAsyncIteration:
                            break
                finally:
                    loop.run_until_complete(async_gen.aclose())
            
            yield from sync_wrapper()
        else:
            # Handle sync generator
            yield from event_generator
    
    def handle_sse_error(self, error: Exception, connection_id: str) -> SSEEvent:
        """Handle SSE connection errors."""
        logger.error(f"SSE error on connection {connection_id}: {str(error)}")
        
        return SSEEvent(
            data={
                "error": "SSE connection error",
                "message": str(error),
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            event_type="error",
            retry=5000  # 5 second retry on error
        )
    
    def create_heartbeat_event(self) -> SSEEvent:
        """Create heartbeat event to keep connection alive."""
        return SSEEvent(
            data={"type": "heartbeat", "timestamp": time.time()},
            event_type="heartbeat",
            retry=30000  # 30 second heartbeat interval
        )
    
    def cleanup_connection(self, connection_id: str):
        """Clean up SSE connection resources."""
        self.sse_connection_manager.remove_connection(connection_id)


class SSEAPIView(APIView, SSEViewMixin):
    """
    API view with built-in SSE support.
    
    Combines DRF APIView with SSE capabilities for easy creation
    of SSE endpoints with authentication and permissions.
    """
    
    def get(self, request: HttpRequest, *args, **kwargs):
        """
        Default GET handler for SSE endpoints.
        
        Override sse_event_stream() method in subclasses to provide
        the actual event stream.
        """
        try:
            event_stream = self.sse_event_stream(request, *args, **kwargs)
            return self.create_sse_response(event_stream, request)
        except Exception as e:
            logger.error(f"SSE endpoint error: {str(e)}")
            return Response(
                {"error": "SSE endpoint error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def sse_event_stream(self, request: HttpRequest, *args, **kwargs) -> Iterator[SSEEvent]:
        """
        Override this method to provide SSE event stream.
        
        Args:
            request: HTTP request object
            *args, **kwargs: URL arguments
            
        Returns:
            Iterator yielding SSEEvent objects
            
        Raises:
            NotImplementedError: If not implemented in subclass
        """
        raise NotImplementedError("Subclasses must implement sse_event_stream()")


# Utility functions for common SSE patterns
def create_simple_sse_response(
    data_list: List[Any],
    event_type: str = "data",
    retry_timeout: int = 3000
) -> SSEResponse:
    """
    Create simple SSE response from list of data.
    
    Args:
        data_list: List of data items to send as events
        event_type: Event type for all events
        retry_timeout: Retry timeout in milliseconds
        
    Returns:
        SSEResponse ready to return from view
    """
    def event_generator():
        for item in data_list:
            yield SSEEvent(data=item, event_type=event_type)
    
    return SSEResponse(
        streaming_content=event_generator(),
        retry_timeout=retry_timeout
    )


async def create_periodic_sse_response(
    data_generator: Callable[[], Any],
    interval_seconds: float = 1.0,
    max_events: Optional[int] = None,
    event_type: str = "update"
) -> SSEResponse:
    """
    Create SSE response that sends periodic updates.
    
    Args:
        data_generator: Function that generates data for each event
        interval_seconds: Seconds between events
        max_events: Maximum number of events to send (None for unlimited)
        event_type: Event type for all events
        
    Returns:
        SSEResponse with periodic events
    """
    async def periodic_event_generator():
        event_count = 0
        
        while max_events is None or event_count < max_events:
            try:
                data = data_generator()
                yield SSEEvent(data=data, event_type=event_type)
                event_count += 1
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                yield SSEEvent(
                    data={"error": str(e)},
                    event_type="error",
                    retry=5000
                )
                break
    
    return SSEResponse(streaming_content=periodic_event_generator())


def create_json_sse_event(data: Dict[str, Any], event_type: str = "data") -> SSEEvent:
    """Create SSE event from JSON data."""
    return SSEEvent(data=data, event_type=event_type)


def create_text_sse_event(text: str, event_type: str = "message") -> SSEEvent:
    """Create SSE event from plain text."""
    return SSEEvent(data=text, event_type=event_type)