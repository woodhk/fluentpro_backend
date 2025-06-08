from rest_framework.response import Response
from rest_framework import status
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator, Union, Callable
from datetime import datetime
import uuid

# Import streaming infrastructure
from .streaming import (
    StreamingJSONResponse,
    AsyncJSONStreamer,
    ProgressTracker,
    stream_large_dataset,
    stream_with_progress
)

class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(
        data: Any,
        message: str = None,
        status_code: int = status.HTTP_200_OK,
        meta: Dict[str, Any] = None
    ) -> Response:
        """Create success response"""
        response_data = {
            "data": data,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "v1",
                **(meta or {})
            }
        }
        
        if message:
            response_data["message"] = message
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        details: List[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: str = None
    ) -> Response:
        """Create error response"""
        return Response({
            "error": {
                "code": code,
                "message": message,
                "details": details or []
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id or str(uuid.uuid4())
            }
        }, status=status_code)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, Any]]) -> Response:
        """Create validation error response"""
        return APIResponse.error(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    async def streaming_response(
        data_source: Union[Iterator, AsyncIterator],
        transform_func: Optional[Callable] = None,
        chunk_size: int = 1000,
        streaming_type: str = "array",
        include_metadata: bool = True
    ) -> StreamingJSONResponse:
        """
        Create streaming JSON response for large datasets.
        
        Args:
            data_source: Iterator or async iterator yielding data items
            transform_func: Optional function to transform each item
            chunk_size: Number of items to process per chunk
            streaming_type: 'array' for JSON array or 'objects' for NDJSON
            include_metadata: Whether to include streaming metadata
            
        Returns:
            StreamingJSONResponse for efficient data streaming
        """
        return await stream_large_dataset(
            data_source=data_source,
            transform_func=transform_func,
            chunk_size=chunk_size,
            streaming_type=streaming_type
        )
    
    @staticmethod
    async def streaming_response_with_progress(
        data_source: Union[Iterator, AsyncIterator],
        total_items: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
        transform_func: Optional[Callable] = None,
        chunk_size: int = 1000
    ) -> tuple[StreamingJSONResponse, ProgressTracker]:
        """
        Create streaming response with progress tracking for long-running tasks.
        
        Args:
            data_source: Iterator or async iterator yielding data items
            total_items: Total number of items (if known) for progress calculation
            progress_callback: Optional callback function for progress updates
            transform_func: Optional function to transform each item
            chunk_size: Number of items to process per chunk
            
        Returns:
            Tuple of (StreamingJSONResponse, ProgressTracker)
        """
        tracker = ProgressTracker(total_items=total_items)
        
        async def tracked_data_source():
            async for item in data_source:
                tracker.update(1)
                if progress_callback:
                    await progress_callback(tracker.get_progress())
                
                if transform_func:
                    item = transform_func(item)
                
                yield item
        
        response = await stream_large_dataset(
            data_source=tracked_data_source(),
            chunk_size=chunk_size
        )
        
        return response, tracker
    
    @staticmethod
    def streaming_array_response(
        data_source: Union[Iterator, AsyncIterator],
        transform_func: Optional[Callable] = None,
        chunk_size: int = 1000,
        headers: Optional[Dict[str, str]] = None
    ) -> StreamingJSONResponse:
        """
        Create streaming response for JSON arrays (synchronous version).
        
        Args:
            data_source: Iterator yielding data items
            transform_func: Optional function to transform each item
            chunk_size: Number of items to process per chunk
            headers: Additional HTTP headers
            
        Returns:
            StreamingJSONResponse with JSON array format
        """
        return StreamingJSONResponse(
            data_source=data_source,
            streaming_type="array",
            transform_func=transform_func,
            chunk_size=chunk_size,
            headers=headers,
            include_metadata=True
        )
    
    @staticmethod
    def streaming_objects_response(
        data_source: Union[Iterator, AsyncIterator],
        transform_func: Optional[Callable] = None,
        chunk_size: int = 1000,
        headers: Optional[Dict[str, str]] = None
    ) -> StreamingJSONResponse:
        """
        Create streaming response for NDJSON objects (synchronous version).
        
        Args:
            data_source: Iterator yielding data items
            transform_func: Optional function to transform each item
            chunk_size: Number of items to process per chunk
            headers: Additional HTTP headers
            
        Returns:
            StreamingJSONResponse with NDJSON format
        """
        return StreamingJSONResponse(
            data_source=data_source,
            streaming_type="objects",
            transform_func=transform_func,
            chunk_size=chunk_size,
            headers=headers,
            include_metadata=True
        )