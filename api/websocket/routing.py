"""WebSocket URL routing configuration."""

from django.urls import re_path

# WebSocket URL patterns will be added here as consumers are created
websocket_urlpatterns = [
    # Example pattern (to be implemented):
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]