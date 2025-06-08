"""
Authenticated REST and WebSocket test clients.
Provides utilities for testing authenticated API endpoints and WebSocket connections.
"""

import json
import jwt
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urlencode

from django.test import Client
from django.contrib.auth import get_user_model
try:
    from channels.testing import WebsocketCommunicator
    from channels.db import database_sync_to_async
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    WebsocketCommunicator = None
    database_sync_to_async = None

from rest_framework.test import APIClient

try:
    from api.websocket.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []


class JWTTestMixin:
    """Mixin for JWT token generation in tests."""
    
    @staticmethod
    def create_test_jwt(
        user_id: str,
        email: str,
        expires_in: int = 3600,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a test JWT token.
        
        Args:
            user_id: User ID (auth0_id)
            email: User email
            expires_in: Token expiration in seconds
            extra_claims: Additional JWT claims
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        payload = {
            'sub': user_id,
            'email': email,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'aud': 'test-audience',
            'iss': 'test-issuer'
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        # Use a test secret for JWT signing
        return jwt.encode(payload, 'test-secret', algorithm='HS256')


class AuthenticatedAPIClient(APIClient, JWTTestMixin):
    """
    Extended APIClient with authentication support.
    Automatically handles JWT token generation and header injection.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_user = None
        self._current_token = None
    
    def authenticate_as(
        self,
        user_id: str = 'test-user-123',
        email: str = 'test@example.com',
        **jwt_kwargs
    ) -> 'AuthenticatedAPIClient':
        """
        Authenticate the client as a specific user.
        
        Args:
            user_id: User ID for authentication
            email: User email
            **jwt_kwargs: Additional arguments for JWT creation
            
        Returns:
            Self for method chaining
        """
        self._current_user = {'id': user_id, 'email': email}
        self._current_token = self.create_test_jwt(user_id, email, **jwt_kwargs)
        self.credentials(HTTP_AUTHORIZATION=f'Bearer {self._current_token}')
        return self
    
    def unauthenticate(self) -> 'AuthenticatedAPIClient':
        """Remove authentication from the client."""
        self._current_user = None
        self._current_token = None
        self.credentials()
        return self
    
    def get_current_token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self._current_token
    
    def get_current_user(self) -> Optional[Dict[str, str]]:
        """Get the current authenticated user info."""
        return self._current_user
    
    def request_with_retries(
        self,
        method: str,
        path: str,
        retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Make a request with automatic retry logic.
        
        Args:
            method: HTTP method
            path: Request path
            retries: Number of retry attempts
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        last_exception = None
        
        for attempt in range(retries):
            try:
                response = getattr(self, method.lower())(path, **kwargs)
                if response.status_code < 500:
                    return response
            except Exception as e:
                last_exception = e
            
            if attempt < retries - 1:
                # Simple exponential backoff
                import time
                time.sleep(0.1 * (2 ** attempt))
        
        if last_exception:
            raise last_exception
        return response
    
    def json_request(
        self,
        method: str,
        path: str,
        data: Optional[Union[Dict, List]] = None,
        **kwargs
    ) -> Any:
        """
        Make a JSON request with proper content type.
        
        Args:
            method: HTTP method
            path: Request path
            data: JSON data to send
            **kwargs: Additional request arguments
            
        Returns:
            Response object
        """
        kwargs.setdefault('content_type', 'application/json')
        
        if data is not None:
            kwargs['data'] = json.dumps(data)
        
        return getattr(self, method.lower())(path, **kwargs)


class AuthenticatedWebSocketClient(JWTTestMixin):
    """
    WebSocket client with authentication support.
    Handles JWT token authentication for WebSocket connections.
    """
    
    def __init__(self):
        if not CHANNELS_AVAILABLE:
            raise ImportError(
                "Django Channels is not installed. "
                "Install it with: pip install channels daphne"
            )
        self._communicator: Optional[WebsocketCommunicator] = None
        self._current_token: Optional[str] = None
        self._current_user: Optional[Dict[str, str]] = None
    
    async def connect(
        self,
        path: str,
        user_id: str = 'test-user-123',
        email: str = 'test@example.com',
        headers: Optional[List[tuple]] = None,
        **jwt_kwargs
    ) -> bool:
        """
        Connect to a WebSocket endpoint with authentication.
        
        Args:
            path: WebSocket path (e.g., '/ws/echo/')
            user_id: User ID for authentication
            email: User email
            headers: Additional headers
            **jwt_kwargs: Additional arguments for JWT creation
            
        Returns:
            True if connection succeeded
        """
        # Generate JWT token
        self._current_user = {'id': user_id, 'email': email}
        self._current_token = self.create_test_jwt(user_id, email, **jwt_kwargs)
        
        # Add token to query string
        query_string = urlencode({'token': self._current_token})
        full_path = f"{path}?{query_string}"
        
        # Find the appropriate consumer
        consumer = None
        for pattern in websocket_urlpatterns:
            if pattern.pattern.match(path.lstrip('/')):
                consumer = pattern.callback
                break
        
        if not consumer:
            raise ValueError(f"No WebSocket consumer found for path: {path}")
        
        # Create communicator
        self._communicator = WebsocketCommunicator(
            consumer.as_asgi(),
            full_path,
            headers=headers or []
        )
        
        # Connect
        connected, _ = await self._communicator.connect()
        return connected
    
    async def disconnect(self, code: int = 1000) -> None:
        """Disconnect from the WebSocket."""
        if self._communicator:
            await self._communicator.disconnect(code)
            self._communicator = None
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data to the WebSocket."""
        if not self._communicator:
            raise RuntimeError("Not connected to WebSocket")
        await self._communicator.send_json_to(data)
    
    async def receive_json(self, timeout: float = 1.0) -> Dict[str, Any]:
        """
        Receive JSON data from the WebSocket.
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            Received JSON data
        """
        if not self._communicator:
            raise RuntimeError("Not connected to WebSocket")
        
        message = await self._communicator.receive_json_from(timeout)
        return message
    
    async def receive_nothing(self, timeout: float = 0.1) -> bool:
        """
        Assert that no message is received within timeout.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if nothing received
        """
        if not self._communicator:
            raise RuntimeError("Not connected to WebSocket")
        
        assert await self._communicator.receive_nothing(timeout)
        return True
    
    def get_current_token(self) -> Optional[str]:
        """Get the current authentication token."""
        return self._current_token
    
    def get_current_user(self) -> Optional[Dict[str, str]]:
        """Get the current authenticated user info."""
        return self._current_user
    
    async def connect_and_authenticate(
        self,
        path: str,
        **auth_kwargs
    ) -> 'AuthenticatedWebSocketClient':
        """
        Connect and authenticate in one step.
        
        Args:
            path: WebSocket path
            **auth_kwargs: Authentication arguments
            
        Returns:
            Self for method chaining
        """
        connected = await self.connect(path, **auth_kwargs)
        if not connected:
            raise RuntimeError(f"Failed to connect to {path}")
        return self


class WebSocketTestSession:
    """
    Context manager for WebSocket testing sessions.
    Automatically handles connection and disconnection.
    """
    
    def __init__(
        self,
        path: str,
        **connect_kwargs
    ):
        self.path = path
        self.connect_kwargs = connect_kwargs
        self.client = AuthenticatedWebSocketClient()
    
    async def __aenter__(self) -> AuthenticatedWebSocketClient:
        """Connect on enter."""
        await self.client.connect(self.path, **self.connect_kwargs)
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Disconnect on exit."""
        await self.client.disconnect()


def create_authenticated_api_client(**auth_kwargs) -> AuthenticatedAPIClient:
    """
    Factory function to create an authenticated API client.
    
    Args:
        **auth_kwargs: Arguments for authentication
        
    Returns:
        Configured AuthenticatedAPIClient
    """
    client = AuthenticatedAPIClient()
    if auth_kwargs:
        client.authenticate_as(**auth_kwargs)
    return client


def create_websocket_client() -> AuthenticatedWebSocketClient:
    """
    Factory function to create a WebSocket client.
    
    Returns:
        New AuthenticatedWebSocketClient instance
    """
    return AuthenticatedWebSocketClient()