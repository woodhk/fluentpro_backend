"""
Streaming response infrastructure for handling large datasets and real-time data flow.

This module provides classes for streaming JSON responses, handling large datasets
without memory issues, and tracking progress for long-running operations.
"""

import json
import asyncio
from typing import AsyncIterator, Iterator, Any, Dict, Optional, Callable, Union
from datetime import datetime
from django.http import StreamingHttpResponse, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.response import Response
from rest_framework import status
import uuid


class StreamingResponse(StreamingHttpResponse):
    """
    Enhanced streaming HTTP response for large datasets.
    
    Provides efficient streaming of large data without loading everything into memory.
    Supports both synchronous and asynchronous data sources.
    """
    
    def __init__(
        self,
        streaming_content: Union[Iterator, AsyncIterator],
        content_type: str = "application/json",
        status: int = 200,
        reason: Optional[str] = None,
        charset: str = "utf-8",
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize streaming response.
        
        Args:
            streaming_content: Iterator or async iterator yielding content chunks
            content_type: MIME type of the response
            status: HTTP status code
            reason: HTTP reason phrase
            charset: Character encoding
            headers: Additional headers to include
        """
        # Convert async iterator to sync if needed for Django compatibility
        if hasattr(streaming_content, '__aiter__'):
            streaming_content = self._async_to_sync_iterator(streaming_content)
        
        super().__init__(
            streaming_content=streaming_content,
            content_type=content_type,
            status=status,
            reason=reason,
            charset=charset
        )
        
        # Add default headers for streaming
        self['Cache-Control'] = 'no-cache'
        self['Connection'] = 'keep-alive'
        
        # Add custom headers
        if headers:
            for key, value in headers.items():
                self[key] = value
    
    def _async_to_sync_iterator(self, async_iter: AsyncIterator) -> Iterator:
        """Convert async iterator to sync iterator for Django compatibility."""
        async def _async_generator():
            async for item in async_iter:
                yield item
        
        # Create a new event loop for this thread if one doesn't exist
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


class AsyncJSONStreamer:
    """
    Asynchronous JSON streaming for large datasets and real-time operations.
    
    Efficiently streams JSON data without loading entire datasets into memory.
    Supports both array streaming and object streaming patterns.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        json_encoder: type = DjangoJSONEncoder,
        include_metadata: bool = True
    ):
        """
        Initialize the JSON streamer.
        
        Args:
            chunk_size: Number of items to process in each chunk
            json_encoder: JSON encoder class to use
            include_metadata: Whether to include streaming metadata
        """
        self.chunk_size = chunk_size
        self.json_encoder = json_encoder
        self.include_metadata = include_metadata
        self.request_id = str(uuid.uuid4())
    
    async def stream_array(
        self,
        data_source: Union[AsyncIterator, Iterator],
        transform_func: Optional[Callable] = None
    ) -> AsyncIterator[str]:
        """
        Stream array data as JSON chunks.
        
        Args:
            data_source: Async iterator or iterator yielding data items
            transform_func: Optional function to transform each item
            
        Yields:
            JSON string chunks
        """
        # Start JSON array
        if self.include_metadata:
            metadata = {
                "request_id": self.request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "streaming": True,
                "chunk_size": self.chunk_size
            }
            yield json.dumps({"meta": metadata, "data": [}, cls=self.json_encoder)[:-2] + ","
        else:
            yield "["
        
        first_item = True
        items_count = 0
        
        # Handle both sync and async iterators
        if hasattr(data_source, '__aiter__'):
            async for item in data_source:
                if not first_item:
                    yield ","
                
                if transform_func:
                    item = transform_func(item)
                
                yield json.dumps(item, cls=self.json_encoder)
                first_item = False
                items_count += 1
                
                # Yield control periodically for async operations
                if items_count % self.chunk_size == 0:
                    await asyncio.sleep(0)
        else:
            # Handle sync iterators
            for item in data_source:
                if not first_item:
                    yield ","
                
                if transform_func:
                    item = transform_func(item)
                
                yield json.dumps(item, cls=self.json_encoder)
                first_item = False
                items_count += 1
                
                # Yield control periodically
                if items_count % self.chunk_size == 0:
                    await asyncio.sleep(0)
        
        # Close JSON array
        if self.include_metadata:
            yield f'],"count":{items_count}}}'
        else:
            yield "]"
    
    async def stream_objects(
        self,
        data_source: Union[AsyncIterator, Iterator],
        transform_func: Optional[Callable] = None
    ) -> AsyncIterator[str]:
        """
        Stream individual objects as newline-delimited JSON (NDJSON).
        
        Args:
            data_source: Async iterator or iterator yielding data items
            transform_func: Optional function to transform each item
            
        Yields:
            NDJSON string chunks (one JSON object per line)
        """
        items_count = 0
        
        # Handle both sync and async iterators
        if hasattr(data_source, '__aiter__'):
            async for item in data_source:
                if transform_func:
                    item = transform_func(item)
                
                yield json.dumps(item, cls=self.json_encoder) + "\n"
                items_count += 1
                
                # Yield control periodically for async operations
                if items_count % self.chunk_size == 0:
                    await asyncio.sleep(0)
        else:
            # Handle sync iterators
            for item in data_source:
                if transform_func:
                    item = transform_func(item)
                
                yield json.dumps(item, cls=self.json_encoder) + "\n"
                items_count += 1
                
                # Yield control periodically
                if items_count % self.chunk_size == 0:
                    await asyncio.sleep(0)


class ProgressTracker:
    """
    Progress tracking for long-running tasks with real-time updates.
    
    Provides progress reporting capabilities for streaming operations,
    AI processing, and other long-running tasks.
    """
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        total_items: Optional[int] = None,
        update_interval: float = 1.0
    ):
        """
        Initialize progress tracker.
        
        Args:
            task_id: Unique identifier for the task
            total_items: Total number of items to process (if known)
            update_interval: Seconds between progress updates
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.total_items = total_items
        self.update_interval = update_interval
        self.processed_items = 0
        self.start_time = datetime.utcnow()
        self.last_update = self.start_time
        self.status = "started"
        self.error_count = 0
        self.custom_metrics = {}
    
    def update(self, items_processed: int = 1, **custom_metrics):
        """
        Update progress with number of items processed.
        
        Args:
            items_processed: Number of items processed since last update
            **custom_metrics: Additional metrics to track
        """
        self.processed_items += items_processed
        self.custom_metrics.update(custom_metrics)
        
        if "errors" in custom_metrics:
            self.error_count += custom_metrics["errors"]
    
    def mark_error(self, error_count: int = 1):
        """Mark errors encountered during processing."""
        self.error_count += error_count
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress information.
        
        Returns:
            Dictionary containing progress metrics
        """
        now = datetime.utcnow()
        elapsed_time = (now - self.start_time).total_seconds()
        
        progress_info = {
            "task_id": self.task_id,
            "status": self.status,
            "processed_items": self.processed_items,
            "error_count": self.error_count,
            "start_time": self.start_time.isoformat(),
            "elapsed_time_seconds": elapsed_time,
            "custom_metrics": self.custom_metrics
        }
        
        if self.total_items:
            progress_info.update({
                "total_items": self.total_items,
                "completion_percentage": (self.processed_items / self.total_items) * 100,
                "estimated_time_remaining": self._estimate_remaining_time(elapsed_time)
            })
        
        if elapsed_time > 0:
            progress_info["items_per_second"] = self.processed_items / elapsed_time
        
        return progress_info
    
    def _estimate_remaining_time(self, elapsed_time: float) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.processed_items == 0 or not self.total_items:
            return None
        
        items_per_second = self.processed_items / elapsed_time
        remaining_items = self.total_items - self.processed_items
        
        if items_per_second > 0:
            return remaining_items / items_per_second
        
        return None
    
    def complete(self, status: str = "completed"):
        """Mark the task as completed."""
        self.status = status
    
    async def stream_progress(self) -> AsyncIterator[str]:
        """
        Stream progress updates as Server-Sent Events.
        
        Yields:
            SSE-formatted progress updates
        """
        while self.status not in ["completed", "failed", "cancelled"]:
            now = datetime.utcnow()
            
            if (now - self.last_update).total_seconds() >= self.update_interval:
                progress = self.get_progress()
                yield f"data: {json.dumps(progress)}\n\n"
                self.last_update = now
            
            await asyncio.sleep(0.1)
        
        # Send final progress update
        final_progress = self.get_progress()
        yield f"data: {json.dumps(final_progress)}\n\n"


class StreamingJSONResponse(StreamingResponse):
    """
    Specialized streaming response for JSON data.
    
    Combines StreamingResponse with AsyncJSONStreamer for easy JSON streaming.
    """
    
    def __init__(
        self,
        data_source: Union[AsyncIterator, Iterator],
        streaming_type: str = "array",
        transform_func: Optional[Callable] = None,
        chunk_size: int = 1000,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        include_metadata: bool = True
    ):
        """
        Initialize streaming JSON response.
        
        Args:
            data_source: Data source iterator
            streaming_type: 'array' for JSON array or 'objects' for NDJSON
            transform_func: Optional transform function for each item
            chunk_size: Number of items per chunk
            status: HTTP status code
            headers: Additional headers
            include_metadata: Whether to include streaming metadata
        """
        self.streamer = AsyncJSONStreamer(
            chunk_size=chunk_size,
            include_metadata=include_metadata
        )
        
        # Choose content type based on streaming type
        content_type = (
            "application/json" if streaming_type == "array"
            else "application/x-ndjson"
        )
        
        # Create the streaming content
        if streaming_type == "array":
            streaming_content = self.streamer.stream_array(data_source, transform_func)
        else:
            streaming_content = self.streamer.stream_objects(data_source, transform_func)
        
        super().__init__(
            streaming_content=streaming_content,
            content_type=content_type,
            status=status,
            headers=headers
        )


# Utility functions for easy streaming response creation
async def stream_large_dataset(
    data_source: Union[AsyncIterator, Iterator],
    transform_func: Optional[Callable] = None,
    chunk_size: int = 1000,
    streaming_type: str = "array"
) -> StreamingJSONResponse:
    """
    Create a streaming JSON response for large datasets.
    
    Args:
        data_source: Iterator yielding data items
        transform_func: Optional function to transform each item
        chunk_size: Number of items to process per chunk
        streaming_type: 'array' for JSON array or 'objects' for NDJSON
        
    Returns:
        StreamingJSONResponse ready to be returned from view
    """
    return StreamingJSONResponse(
        data_source=data_source,
        streaming_type=streaming_type,
        transform_func=transform_func,
        chunk_size=chunk_size,
        include_metadata=True
    )


async def stream_with_progress(
    data_source: Union[AsyncIterator, Iterator],
    total_items: Optional[int] = None,
    progress_callback: Optional[Callable] = None
) -> tuple[StreamingJSONResponse, ProgressTracker]:
    """
    Create a streaming response with progress tracking.
    
    Args:
        data_source: Iterator yielding data items
        total_items: Total number of items (if known)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (StreamingJSONResponse, ProgressTracker)
    """
    tracker = ProgressTracker(total_items=total_items)
    
    async def tracked_data_source():
        async for item in data_source:
            tracker.update(1)
            if progress_callback:
                await progress_callback(tracker.get_progress())
            yield item
    
    response = await stream_large_dataset(tracked_data_source())
    return response, tracker