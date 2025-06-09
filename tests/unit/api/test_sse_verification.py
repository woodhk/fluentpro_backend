"""
Server-Sent Events (SSE) verification and demonstration.

This module provides test views and examples to verify that SSE endpoints
work correctly with browser clients and handle various scenarios.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Any, Dict, Iterator

from django.http import HttpRequest, HttpResponse
from rest_framework.permissions import AllowAny

from .async_views import AsyncAPIView
from .sse import (
    SSEAPIView,
    SSEEvent,
    SSEViewMixin,
    create_json_sse_event,
    create_periodic_sse_response,
    create_simple_sse_response,
    create_text_sse_event,
)


class SimpleSSEView(SSEAPIView):
    """
    Simple SSE endpoint for basic verification.

    Streams a series of numbered events to demonstrate basic SSE functionality.
    """

    permission_classes = [AllowAny]  # For testing purposes only

    def sse_event_stream(
        self, request: HttpRequest, *args, **kwargs
    ) -> Iterator[SSEEvent]:
        """Stream simple numbered events."""
        count = int(request.GET.get("count", 10))
        interval = float(request.GET.get("interval", 1.0))

        for i in range(count):
            yield SSEEvent(
                data={
                    "message": f"Event number {i + 1}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_number": i + 1,
                    "total_events": count,
                },
                event_type="counter",
                event_id=f"event_{i + 1}",
            )

            # Simulate delay between events
            time.sleep(interval)

        # Send completion event
        yield SSEEvent(
            data={
                "message": "Stream completed",
                "total_sent": count,
                "timestamp": datetime.utcnow().isoformat(),
            },
            event_type="complete",
            event_id="complete",
        )


class ProgressSSEView(SSEAPIView):
    """
    SSE endpoint demonstrating progress tracking.

    Simulates a long-running task with progress updates via SSE.
    """

    permission_classes = [AllowAny]  # For testing purposes only

    def sse_event_stream(
        self, request: HttpRequest, *args, **kwargs
    ) -> Iterator[SSEEvent]:
        """Stream progress updates for a simulated task."""
        total_steps = int(request.GET.get("steps", 20))
        delay = float(request.GET.get("delay", 0.5))

        # Send start event
        yield SSEEvent(
            data={
                "status": "started",
                "total_steps": total_steps,
                "message": "Task started",
            },
            event_type="progress",
            event_id="start",
        )

        # Send progress updates
        for step in range(1, total_steps + 1):
            progress_percent = (step / total_steps) * 100

            yield SSEEvent(
                data={
                    "status": "in_progress",
                    "current_step": step,
                    "total_steps": total_steps,
                    "progress_percent": round(progress_percent, 1),
                    "message": f"Processing step {step} of {total_steps}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                event_type="progress",
                event_id=f"step_{step}",
                retry=1000,  # 1 second retry
            )

            time.sleep(delay)

        # Send completion event
        yield SSEEvent(
            data={
                "status": "completed",
                "progress_percent": 100,
                "message": "Task completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            },
            event_type="complete",
            event_id="complete",
        )


class LiveDataSSEView(SSEAPIView):
    """
    SSE endpoint demonstrating live data streaming.

    Streams simulated real-time data like metrics, logs, or sensor readings.
    """

    permission_classes = [AllowAny]  # For testing purposes only

    def sse_event_stream(
        self, request: HttpRequest, *args, **kwargs
    ) -> Iterator[SSEEvent]:
        """Stream live data updates."""
        duration = int(request.GET.get("duration", 30))  # seconds
        interval = float(request.GET.get("interval", 2.0))  # seconds between updates
        data_type = request.GET.get("type", "metrics")

        start_time = time.time()
        event_count = 0

        while (time.time() - start_time) < duration:
            event_count += 1

            if data_type == "metrics":
                data = self._generate_metrics_data(event_count)
                event_type = "metrics"
            elif data_type == "logs":
                data = self._generate_log_data(event_count)
                event_type = "log"
            else:
                data = self._generate_sensor_data(event_count)
                event_type = "sensor"

            yield SSEEvent(
                data=data,
                event_type=event_type,
                event_id=f"{data_type}_{event_count}",
                retry=2000,
            )

            time.sleep(interval)

        # Send end of stream event
        yield SSEEvent(
            data={
                "message": "Live data stream ended",
                "events_sent": event_count,
                "duration": duration,
            },
            event_type="stream_end",
            event_id="end",
        )

    def _generate_metrics_data(self, event_count: int) -> Dict[str, Any]:
        """Generate simulated metrics data."""
        return {
            "cpu_usage": random.uniform(10, 90),
            "memory_usage": random.uniform(30, 80),
            "disk_usage": random.uniform(20, 70),
            "network_in": random.randint(100, 1000),
            "network_out": random.randint(50, 800),
            "timestamp": datetime.utcnow().isoformat(),
            "event_number": event_count,
        }

    def _generate_log_data(self, event_count: int) -> Dict[str, Any]:
        """Generate simulated log data."""
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        log_messages = [
            "User authentication successful",
            "Database connection established",
            "Cache miss for key 'user_123'",
            "Processing request completed",
            "Background task started",
            "File upload completed",
        ]

        return {
            "level": random.choice(log_levels),
            "message": random.choice(log_messages),
            "module": f"module_{random.randint(1, 5)}",
            "user_id": f"user_{random.randint(100, 999)}",
            "timestamp": datetime.utcnow().isoformat(),
            "event_number": event_count,
        }

    def _generate_sensor_data(self, event_count: int) -> Dict[str, Any]:
        """Generate simulated sensor data."""
        return {
            "temperature": round(random.uniform(18, 28), 1),
            "humidity": round(random.uniform(40, 70), 1),
            "pressure": round(random.uniform(1010, 1025), 1),
            "light_level": random.randint(100, 1000),
            "motion_detected": random.choice([True, False]),
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_id": f"sensor_{random.randint(1, 3)}",
            "event_number": event_count,
        }


class ChatSSEView(SSEAPIView):
    """
    SSE endpoint demonstrating chat-like messaging.

    Simulates AI chat responses with typing indicators and message chunks.
    """

    permission_classes = [AllowAny]  # For testing purposes only

    def sse_event_stream(
        self, request: HttpRequest, *args, **kwargs
    ) -> Iterator[SSEEvent]:
        """Stream chat-like conversation."""
        user_message = request.GET.get("message", "Hello!")

        # Send typing indicator
        yield SSEEvent(
            data={
                "type": "typing",
                "message": "AI is typing...",
                "user_message": user_message,
            },
            event_type="typing",
            event_id="typing_start",
        )

        time.sleep(1)  # Simulate thinking time

        # Generate AI response
        ai_response = self._generate_ai_response(user_message)

        # Stream response in chunks (simulating streaming AI)
        words = ai_response.split()
        current_text = ""

        for i, word in enumerate(words):
            current_text += word + " "

            yield SSEEvent(
                data={
                    "type": "message_chunk",
                    "chunk": word + " ",
                    "full_text": current_text.strip(),
                    "is_complete": i == len(words) - 1,
                    "chunk_index": i,
                },
                event_type="message",
                event_id=f"chunk_{i}",
                retry=1000,
            )

            time.sleep(0.2)  # Simulate typing speed

        # Send completion event
        yield SSEEvent(
            data={
                "type": "message_complete",
                "full_message": ai_response,
                "user_message": user_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
            event_type="complete",
            event_id="message_complete",
        )

    def _generate_ai_response(self, user_message: str) -> str:
        """Generate simulated AI response."""
        responses = [
            f"Thank you for your message: '{user_message}'. I understand what you're saying.",
            f"That's an interesting point about '{user_message}'. Let me think about that.",
            f"I see you mentioned '{user_message}'. Here's my response to that.",
            f"Regarding '{user_message}', I think this is a great topic to discuss.",
            f"Your message '{user_message}' reminds me of something important.",
        ]

        return random.choice(responses)


class ReconnectionTestSSEView(SSEAPIView):
    """
    SSE endpoint for testing reconnection behavior.

    Demonstrates how SSE handles client reconnections and missed events.
    """

    permission_classes = [AllowAny]  # For testing purposes only

    def sse_event_stream(
        self, request: HttpRequest, *args, **kwargs
    ) -> Iterator[SSEEvent]:
        """Stream events with built-in disconnection testing."""
        # Check if this is a reconnection
        last_event_id = self.get_last_event_id(request)

        if last_event_id:
            # Send reconnection acknowledgment
            yield SSEEvent(
                data={
                    "message": f"Reconnected! Last event was: {last_event_id}",
                    "reconnection": True,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                event_type="reconnection",
                event_id="reconnection_ack",
            )

        # Stream numbered events
        event_count = int(request.GET.get("count", 20))
        disconnect_at = int(
            request.GET.get("disconnect_at", event_count + 1)
        )  # No disconnect by default

        for i in range(1, event_count + 1):
            # Simulate disconnection
            if i == disconnect_at:
                yield SSEEvent(
                    data={
                        "message": "Simulating connection drop",
                        "disconnect_simulation": True,
                    },
                    event_type="disconnect",
                    event_id=f"disconnect_{i}",
                    retry=2000,  # Retry in 2 seconds
                )
                break  # Simulate connection drop

            yield SSEEvent(
                data={
                    "message": f"Event {i} of {event_count}",
                    "event_number": i,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                event_type="data",
                event_id=f"event_{i}",
                retry=3000,
            )

            time.sleep(1)


# HTML client examples for browser testing
SSE_CLIENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SSE Client Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .event { margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .counter { background-color: #e7f3ff; }
        .progress { background-color: #f0fff0; }
        .error { background-color: #ffe7e7; }
        .complete { background-color: #fff2e7; }
        .status { margin: 10px 0; font-weight: bold; }
        button { margin: 5px; padding: 10px; }
    </style>
</head>
<body>
    <h1>Server-Sent Events Test Client</h1>
    
    <div class="status" id="status">Not connected</div>
    
    <div>
        <button onclick="testSimpleSSE()">Test Simple SSE</button>
        <button onclick="testProgressSSE()">Test Progress SSE</button>
        <button onclick="testLiveData()">Test Live Data</button>
        <button onclick="testChat()">Test Chat SSE</button>
        <button onclick="testReconnection()">Test Reconnection</button>
        <button onclick="disconnect()">Disconnect</button>
        <button onclick="clearEvents()">Clear Events</button>
    </div>
    
    <div id="events"></div>
    
    <script>
        let eventSource = null;
        let eventCount = 0;
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
        
        function addEvent(event, data) {
            const eventsDiv = document.getElementById('events');
            const eventDiv = document.createElement('div');
            eventDiv.className = `event ${event.type}`;
            eventDiv.innerHTML = `
                <strong>Event:</strong> ${event.type}<br>
                <strong>ID:</strong> ${event.lastEventId}<br>
                <strong>Data:</strong> <pre>${JSON.stringify(data, null, 2)}</pre>
                <strong>Time:</strong> ${new Date().toLocaleTimeString()}
            `;
            eventsDiv.appendChild(eventDiv);
            eventCount++;
        }
        
        function connectSSE(url) {
            disconnect(); // Close existing connection
            
            updateStatus(`Connecting to ${url}...`);
            eventSource = new EventSource(url);
            
            eventSource.onopen = function(event) {
                updateStatus('Connected');
            };
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            };
            
            eventSource.addEventListener('counter', function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            });
            
            eventSource.addEventListener('progress', function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            });
            
            eventSource.addEventListener('complete', function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            });
            
            eventSource.addEventListener('metrics', function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            });
            
            eventSource.addEventListener('message', function(event) {
                const data = JSON.parse(event.data);
                addEvent(event, data);
            });
            
            eventSource.onerror = function(event) {
                updateStatus('Connection error');
                addEvent({type: 'error', lastEventId: 'error'}, {
                    message: 'SSE connection error',
                    readyState: eventSource.readyState
                });
            };
        }
        
        function testSimpleSSE() {
            connectSSE('/api/test/sse/simple/?count=5&interval=1');
        }
        
        function testProgressSSE() {
            connectSSE('/api/test/sse/progress/?steps=10&delay=0.5');
        }
        
        function testLiveData() {
            connectSSE('/api/test/sse/live/?duration=15&interval=2&type=metrics');
        }
        
        function testChat() {
            const message = prompt('Enter your message:', 'Hello AI!');
            if (message) {
                connectSSE(`/api/test/sse/chat/?message=${encodeURIComponent(message)}`);
            }
        }
        
        function testReconnection() {
            connectSSE('/api/test/sse/reconnection/?count=15&disconnect_at=8');
        }
        
        function disconnect() {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
                updateStatus('Disconnected');
            }
        }
        
        function clearEvents() {
            document.getElementById('events').innerHTML = '';
            eventCount = 0;
        }
    </script>
</body>
</html>
"""


def get_sse_test_client_html(request: HttpRequest) -> HttpResponse:
    """Return HTML test client for SSE verification."""
    return HttpResponse(SSE_CLIENT_HTML, content_type="text/html")


# URL patterns for verification (example)
"""
# Add these to your urls.py for testing:

from django.urls import path
from .test_sse_verification import (
    SimpleSSEView,
    ProgressSSEView,
    LiveDataSSEView,
    ChatSSEView,
    ReconnectionTestSSEView,
    get_sse_test_client_html
)

urlpatterns = [
    # SSE test endpoints
    path('test/sse/simple/', SimpleSSEView.as_view(), name='test-sse-simple'),
    path('test/sse/progress/', ProgressSSEView.as_view(), name='test-sse-progress'),
    path('test/sse/live/', LiveDataSSEView.as_view(), name='test-sse-live'),
    path('test/sse/chat/', ChatSSEView.as_view(), name='test-sse-chat'),
    path('test/sse/reconnection/', ReconnectionTestSSEView.as_view(), name='test-sse-reconnection'),
    
    # HTML test client
    path('test/sse/client/', get_sse_test_client_html, name='test-sse-client'),
]
"""


# Verification checklist
VERIFICATION_CHECKLIST = """
SSE Verification Checklist:

✅ Basic SSE functionality:
   - Navigate to /test/sse/client/
   - Click "Test Simple SSE"
   - Verify events appear in real-time

✅ Progress tracking:
   - Click "Test Progress SSE"
   - Verify progress updates from 0% to 100%

✅ Live data streaming:
   - Click "Test Live Data"
   - Verify metrics update every 2 seconds for 15 seconds

✅ Chat simulation:
   - Click "Test Chat SSE"
   - Enter a message
   - Verify typing indicator and word-by-word streaming

✅ Reconnection handling:
   - Click "Test Reconnection"
   - Connection should drop at event 8
   - Browser should automatically reconnect
   - Verify "Reconnected!" message appears

✅ Error handling:
   - Disconnect manually during streaming
   - Verify error events appear
   - Verify browser attempts reconnection

✅ Browser compatibility:
   - Test in Chrome, Firefox, Safari, Edge
   - Verify EventSource API works correctly
   - Check developer console for errors

✅ Performance:
   - Test with high-frequency events
   - Verify no memory leaks during long streams
   - Check server resource usage
"""
