"""WebSocket URL routing configuration."""

from django.urls import re_path
from . import consumers

# WebSocket URL patterns for real-time communication
websocket_urlpatterns = [
    # Echo WebSocket for testing basic connectivity
    re_path(r'ws/echo/$', consumers.EchoConsumer.as_asgi()),
    
    # Health check WebSocket for monitoring
    re_path(r'ws/health/$', consumers.HealthCheckConsumer.as_asgi()),
    
    # Room-based WebSocket for group communication
    re_path(r'ws/room/(?P<room_name>\w+)/$', consumers.TestRoomConsumer.as_asgi()),
    
    # Future patterns will be added here as needed:
    # re_path(r'ws/ai/chat/$', consumers.AIChatConsumer.as_asgi()),
    # re_path(r'ws/onboarding/(?P<session_id>\w+)/$', consumers.OnboardingConsumer.as_asgi()),
]