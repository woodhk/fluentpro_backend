"""WebSocket JWT authentication for Auth0 tokens."""

import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from authentication.backends import Auth0JWTAuthentication, SimpleUser

logger = logging.getLogger(__name__)


class WebSocketAuth0Authentication:
    """Handle Auth0 JWT authentication for WebSocket connections."""
    
    def __init__(self):
        self.jwt_auth = Auth0JWTAuthentication()
    
    @database_sync_to_async
    def authenticate_websocket(self, scope):
        """
        Authenticate WebSocket connection using JWT token from query string.
        
        WebSocket connections cannot use Authorization headers, so we expect
        the token to be passed as a query parameter: ?token=<jwt_token>
        """
        try:
            # Extract token from query string
            query_string = scope.get('query_string', b'').decode('utf-8')
            query_params = parse_qs(query_string)
            token_list = query_params.get('token', [])
            
            if not token_list:
                logger.warning("No token provided in WebSocket connection")
                return AnonymousUser()
            
            token = token_list[0]
            
            # Verify the token using the existing Auth0 backend
            payload = self.jwt_auth.verify_token(token)
            
            # Create user from payload
            user = self.jwt_auth.get_or_create_user(payload)
            
            logger.info(f"WebSocket authenticated for user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {str(e)}")
            return AnonymousUser()
    
    @database_sync_to_async
    def get_user_from_scope(self, scope):
        """
        Get user from scope if already authenticated.
        """
        user = scope.get('user', AnonymousUser())
        return user