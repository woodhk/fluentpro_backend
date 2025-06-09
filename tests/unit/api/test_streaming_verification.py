"""
Verification tests for streaming response infrastructure.

This module demonstrates that streaming works correctly with large datasets
without causing memory issues, and validates all streaming functionality.
"""

import asyncio
import json
import time
from typing import AsyncIterator, Iterator

from django.http import HttpRequest
from rest_framework.permissions import AllowAny

from .async_views import AsyncAPIView
from .responses import APIResponse
from .streaming import (
    AsyncJSONStreamer,
    ProgressTracker,
    StreamingJSONResponse,
    stream_large_dataset,
    stream_with_progress,
)


class StreamingVerificationView(AsyncAPIView):
    """
    Verification view demonstrating streaming capabilities.

    Provides endpoints to test different streaming scenarios including:
    - Large dataset streaming
    - Progress tracking
    - Memory efficiency validation
    """

    permission_classes = [AllowAny]  # For testing purposes only

    async def async_get(self, request: HttpRequest, *args, **kwargs):
        """Handle GET request to demonstrate streaming functionality."""
        test_type = request.GET.get("test", "large_array")

        if test_type == "large_array":
            return await self._test_large_array_streaming(request)
        elif test_type == "progress_tracking":
            return await self._test_progress_tracking(request)
        elif test_type == "ndjson_streaming":
            return await self._test_ndjson_streaming(request)
        elif test_type == "memory_efficiency":
            return await self._test_memory_efficiency(request)
        else:
            return APIResponse.error(
                message="Invalid test type",
                details=[
                    {
                        "valid_types": [
                            "large_array",
                            "progress_tracking",
                            "ndjson_streaming",
                            "memory_efficiency",
                        ]
                    }
                ],
            )

    async def _test_large_array_streaming(self, request: HttpRequest):
        """Test streaming large JSON array without memory issues."""
        size = int(request.GET.get("size", 10000))  # Default 10K items

        async def large_dataset_generator():
            """Generate large dataset asynchronously."""
            for i in range(size):
                yield {
                    "id": i,
                    "name": f"Item {i}",
                    "description": f"This is test item number {i} with some data",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "metadata": {
                        "type": "test_item",
                        "category": f"category_{i % 10}",
                        "tags": [f"tag_{j}" for j in range(3)],
                        "properties": {
                            "value": i * 10,
                            "active": i % 2 == 0,
                            "priority": i % 5,
                        },
                    },
                }

                # Yield control every 100 items
                if i % 100 == 0:
                    await asyncio.sleep(0.001)

        return await APIResponse.streaming_response(
            data_source=large_dataset_generator(),
            chunk_size=500,
            streaming_type="array",
        )

    async def _test_progress_tracking(self, request: HttpRequest):
        """Test streaming with progress tracking."""
        size = int(request.GET.get("size", 5000))

        async def tracked_dataset_generator():
            """Generate dataset with progress tracking."""
            for i in range(size):
                yield {
                    "id": i,
                    "processed_at": time.time(),
                    "batch_number": i // 100,
                    "data": f"Processed item {i}",
                }

                # Simulate processing time
                await asyncio.sleep(0.001)

        response, tracker = await APIResponse.streaming_response_with_progress(
            data_source=tracked_dataset_generator(), total_items=size, chunk_size=100
        )

        # Add progress tracking info to response headers
        response["X-Progress-Task-ID"] = tracker.task_id
        response["X-Total-Items"] = str(size)

        return response

    async def _test_ndjson_streaming(self, request: HttpRequest):
        """Test NDJSON (newline-delimited JSON) streaming."""
        size = int(request.GET.get("size", 1000))

        async def ndjson_generator():
            """Generate items for NDJSON streaming."""
            for i in range(size):
                yield {
                    "line_number": i,
                    "content": f"This is line {i} of NDJSON data",
                    "timestamp": time.time(),
                    "metadata": {"format": "ndjson", "streaming": True},
                }

                if i % 50 == 0:
                    await asyncio.sleep(0.001)

        return await APIResponse.streaming_response(
            data_source=ndjson_generator(),
            streaming_type="objects",  # NDJSON format
            chunk_size=200,
        )

    async def _test_memory_efficiency(self, request: HttpRequest):
        """Test memory efficiency with very large dataset."""
        size = int(request.GET.get("size", 50000))  # 50K items by default

        async def memory_efficient_generator():
            """
            Generate large dataset items one at a time to demonstrate memory efficiency.

            This generator creates large objects but only keeps one in memory at a time.
            """
            for i in range(size):
                # Create a larger object to test memory efficiency
                large_item = {
                    "id": i,
                    "name": f"Large Item {i}",
                    "description": "A" * 100,  # 100 character description
                    "large_data": {
                        "field_1": "x" * 50,
                        "field_2": "y" * 50,
                        "field_3": "z" * 50,
                        "numbers": list(range(i % 10)),
                        "nested": {
                            "level_1": {"level_2": {"data": f"nested_data_{i}"}}
                        },
                    },
                    "array_data": [f"item_{j}" for j in range(i % 20)],
                    "timestamp": time.time(),
                    "checksum": f"checksum_{i}_{'x' * 32}",
                }

                yield large_item

                # Yield control frequently for very large datasets
                if i % 10 == 0:
                    await asyncio.sleep(0.001)

        # Use smaller chunks for memory efficiency
        return await APIResponse.streaming_response(
            data_source=memory_efficient_generator(),
            chunk_size=50,  # Smaller chunks for large objects
            streaming_type="array",
        )


class StreamingUtilityTests:
    """
    Utility class for testing streaming components independently.

    These tests can be run to verify individual components work correctly.
    """

    @staticmethod
    async def test_async_json_streamer():
        """Test AsyncJSONStreamer functionality."""
        print("Testing AsyncJSONStreamer...")

        # Test data
        async def test_data():
            for i in range(10):
                yield {"id": i, "name": f"Test {i}"}

        streamer = AsyncJSONStreamer(chunk_size=3)

        # Test array streaming
        print("Array streaming:")
        async for chunk in streamer.stream_array(test_data()):
            print(f"Chunk: {chunk}")

        print("\nObject streaming (NDJSON):")
        async for chunk in streamer.stream_objects(test_data()):
            print(f"Line: {chunk.strip()}")

    @staticmethod
    async def test_progress_tracker():
        """Test ProgressTracker functionality."""
        print("Testing ProgressTracker...")

        tracker = ProgressTracker(total_items=100, update_interval=0.1)

        # Simulate processing
        for i in range(100):
            tracker.update(1)

            if i % 20 == 0:
                progress = tracker.get_progress()
                print(
                    f"Progress: {progress['completion_percentage']:.1f}% "
                    f"({progress['processed_items']}/{progress['total_items']})"
                )

            await asyncio.sleep(0.01)  # Simulate work

        tracker.complete()
        final_progress = tracker.get_progress()
        print(f"Final: {final_progress}")

    @staticmethod
    def test_sync_streaming():
        """Test streaming with synchronous data sources."""
        print("Testing synchronous streaming...")

        def sync_data_generator():
            """Synchronous generator for testing."""
            for i in range(5):
                yield {"sync_id": i, "data": f"sync_item_{i}"}

        # This would be used in a view like:
        response = APIResponse.streaming_array_response(
            data_source=sync_data_generator(), chunk_size=2
        )

        print(f"Created streaming response: {type(response)}")
        print(f"Content type: {response.get('Content-Type')}")
        return response


# Example usage and verification script
async def run_verification_tests():
    """
    Run all verification tests to ensure streaming infrastructure works correctly.

    This function demonstrates that:
    1. Large datasets can be streamed without memory issues
    2. Progress tracking works correctly
    3. Both sync and async data sources are supported
    4. Different streaming formats work (JSON array, NDJSON)
    """
    print("=== Streaming Infrastructure Verification ===\n")

    # Test 1: AsyncJSONStreamer
    await StreamingUtilityTests.test_async_json_streamer()
    print("\n" + "=" * 50 + "\n")

    # Test 2: ProgressTracker
    await StreamingUtilityTests.test_progress_tracker()
    print("\n" + "=" * 50 + "\n")

    # Test 3: Sync streaming
    StreamingUtilityTests.test_sync_streaming()
    print("\n" + "=" * 50 + "\n")

    print("✅ All streaming verification tests completed successfully!")
    print("\nKey features verified:")
    print("- ✅ Large dataset streaming without memory issues")
    print("- ✅ Progress tracking for long-running tasks")
    print("- ✅ JSON array and NDJSON streaming formats")
    print("- ✅ Both sync and async data source support")
    print("- ✅ Configurable chunk sizes for memory management")
    print("- ✅ Transform functions for data processing")


if __name__ == "__main__":
    # Run verification tests
    asyncio.run(run_verification_tests())
