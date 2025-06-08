"""Base WebSocket consumer with Auth0 JWT authentication."""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from api.websocket.authentication import WebSocketAuth0Authentication

logger = logging.getLogger(__name__)


class BaseAuthenticatedConsumer(AsyncWebsocketConsumer):
    """
    Base WebSocket consumer with Auth0 JWT authentication.
    
    All WebSocket consumers should inherit from this class to ensure
    proper authentication and connection lifecycle management.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = WebSocketAuth0Authentication()
        self.user = None
        self.room_group_name = None
    
    async def connect(self):
        """
        Handle WebSocket connection with authentication.
        """
        try:
            # Authenticate the connection
            self.user = await self.auth_service.authenticate_websocket(self.scope)
            
            if self.user.is_anonymous:
                logger.warning(f"Unauthenticated WebSocket connection attempt from {self.scope['client']}")
                await self.close(code=4001)  # 4001 = authentication failed
                return
            
            # Add user to scope for future use
            self.scope['user'] = self.user
            
            logger.info(f"WebSocket connection established for user: {self.user.email}")
            
            # Accept the connection
            await self.accept()
            
            # Perform any additional setup after connection
            await self.on_connect()
            
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {str(e)}")
            await self.close(code=4000)  # 4000 = generic error
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        try:
            if self.user and not self.user.is_anonymous:
                logger.info(f"WebSocket disconnected for user: {self.user.email} (code: {close_code})")
            
            # Perform cleanup before disconnection
            await self.on_disconnect(close_code)
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {str(e)}")
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages with error handling.
        """
        try:
            # Parse JSON message
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from {self.user.email}: {str(e)}")
                await self.send_error("Invalid JSON format")
                return
            
            # Validate message structure
            if not isinstance(data, dict):
                await self.send_error("Message must be a JSON object")
                return
            
            message_type = data.get('type')
            if not message_type:
                await self.send_error("Message must include 'type' field")
                return
            
            # Handle the message
            await self.handle_message(message_type, data)
            
        except Exception as e:
            logger.error(f"Error handling message from {self.user.email}: {str(e)}")
            await self.send_error("Internal server error")
    
    async def send_message(self, message_type, data=None):
        """
        Send a structured message to the client.
        """
        try:
            message = {
                'type': message_type,
                'timestamp': self.get_timestamp(),
            }
            
            if data:
                message['data'] = data
            
            await self.send(text_data=json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error sending message to {self.user.email}: {str(e)}")
    
    async def send_error(self, error_message, error_code=None):
        """
        Send an error message to the client.
        """
        error_data = {
            'message': error_message,
        }
        
        if error_code:
            error_data['code'] = error_code
        
        await self.send_message('error', error_data)
    
    def get_timestamp(self):
        """
        Get current timestamp in ISO format.
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    # Override methods for specific consumer implementations
    
    async def on_connect(self):
        """
        Called after successful authentication and connection acceptance.
        Override in subclasses for specific connection handling.
        """
        pass
    
    async def on_disconnect(self, close_code):
        """
        Called before disconnection cleanup.
        Override in subclasses for specific disconnection handling.
        """
        pass
    
    async def handle_message(self, message_type, data):
        """
        Handle incoming messages based on type.
        Override in subclasses to handle specific message types.
        """
        logger.warning(f"Unhandled message type '{message_type}' from {self.user.email}")
        await self.send_error(f"Unknown message type: {message_type}")


class BaseRoomConsumer(BaseAuthenticatedConsumer):
    """
    Base consumer for room-based WebSocket connections.
    
    Provides room joining/leaving functionality with proper cleanup.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
    
    async def on_connect(self):
        """
        Join the room after connection.
        """
        self.room_name = self.get_room_name()
        
        if not self.room_name:
            logger.error(f"No room name provided for user {self.user.email}")
            await self.close(code=4003)  # 4003 = missing room
            return
        
        self.room_group_name = f"room_{self.room_name}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.email} joined room: {self.room_name}")
        await self.on_room_join()
    
    async def on_disconnect(self, close_code):
        """
        Leave the room before disconnection.
        """
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            logger.info(f"User {self.user.email} left room: {self.room_name}")
            await self.on_room_leave()
    
    async def send_to_room(self, message_type, data=None):
        """
        Send a message to all clients in the room.
        """
        if not self.room_group_name:
            logger.error("Cannot send to room: no room group name")
            return
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_message',
                'message_type': message_type,
                'data': data,
                'sender': self.user.email
            }
        )
    
    async def room_message(self, event):
        """
        Handle messages sent to the room group.
        """
        await self.send_message(
            event['message_type'],
            event.get('data')
        )
    
    def get_room_name(self):
        """
        Extract room name from URL parameters.
        Override in subclasses to customize room naming.
        """
        return self.scope['url_route']['kwargs'].get('room_name')
    
    async def on_room_join(self):
        """
        Called after joining a room.
        Override in subclasses for room-specific join handling.
        """
        pass
    
    async def on_room_leave(self):
        """
        Called before leaving a room.
        Override in subclasses for room-specific leave handling.
        """
        pass