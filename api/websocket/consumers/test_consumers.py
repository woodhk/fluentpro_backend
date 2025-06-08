"""Test WebSocket consumers for routing verification."""

import logging
from .base_consumer import BaseAuthenticatedConsumer, BaseRoomConsumer

logger = logging.getLogger(__name__)


class EchoConsumer(BaseAuthenticatedConsumer):
    """
    Simple echo consumer for testing WebSocket connectivity.
    
    Echoes back any messages received from the client.
    """
    
    async def on_connect(self):
        """Send welcome message on connection."""
        await self.send_message('welcome', {
            'message': f'Connected successfully as {self.user.email}',
            'user_id': self.user.auth0_id
        })
        
        logger.info(f"Echo consumer connected for user: {self.user.email}")
    
    async def handle_message(self, message_type, data):
        """Echo back the received message."""
        if message_type == 'echo':
            message_content = data.get('message', '')
            
            await self.send_message('echo_response', {
                'original_message': message_content,
                'echo': f"Echo: {message_content}",
                'user': self.user.email
            })
            
            logger.debug(f"Echoed message for {self.user.email}: {message_content}")
        
        elif message_type == 'ping':
            await self.send_message('pong', {
                'timestamp': self.get_timestamp()
            })
        
        else:
            # Let parent handle unknown message types
            await super().handle_message(message_type, data)


class TestRoomConsumer(BaseRoomConsumer):
    """
    Test room consumer for testing room-based WebSocket functionality.
    
    Allows users to join rooms and broadcast messages to all room members.
    """
    
    async def on_room_join(self):
        """Notify room when user joins."""
        await self.send_to_room('user_joined', {
            'user_email': self.user.email,
            'user_id': self.user.auth0_id,
            'room_name': self.room_name,
            'message': f'{self.user.email} joined the room'
        })
        
        await self.send_message('room_joined', {
            'room_name': self.room_name,
            'message': f'You joined room: {self.room_name}'
        })
        
        logger.info(f"User {self.user.email} joined room: {self.room_name}")
    
    async def on_room_leave(self):
        """Notify room when user leaves."""
        await self.send_to_room('user_left', {
            'user_email': self.user.email,
            'user_id': self.user.auth0_id,
            'room_name': self.room_name,
            'message': f'{self.user.email} left the room'
        })
        
        logger.info(f"User {self.user.email} left room: {self.room_name}")
    
    async def handle_message(self, message_type, data):
        """Handle room-specific messages."""
        if message_type == 'room_message':
            message_content = data.get('message', '')
            
            # Broadcast message to all room members
            await self.send_to_room('room_broadcast', {
                'sender': self.user.email,
                'message': message_content,
                'room_name': self.room_name,
                'timestamp': self.get_timestamp()
            })
            
            logger.debug(f"Room {self.room_name} message from {self.user.email}: {message_content}")
        
        elif message_type == 'room_info':
            # Send room information
            await self.send_message('room_info_response', {
                'room_name': self.room_name,
                'user_email': self.user.email,
                'user_id': self.user.auth0_id
            })
        
        else:
            # Let parent handle unknown message types
            await super().handle_message(message_type, data)


class HealthCheckConsumer(BaseAuthenticatedConsumer):
    """
    Health check consumer for monitoring WebSocket connectivity.
    
    Provides basic health check functionality for monitoring systems.
    """
    
    async def on_connect(self):
        """Send health status on connection."""
        await self.send_message('health_status', {
            'status': 'healthy',
            'server_time': self.get_timestamp(),
            'user': self.user.email
        })
        
        logger.info(f"Health check consumer connected for user: {self.user.email}")
    
    async def handle_message(self, message_type, data):
        """Handle health check messages."""
        if message_type == 'health_check':
            await self.send_message('health_response', {
                'status': 'healthy',
                'server_time': self.get_timestamp(),
                'uptime': 'available'  # Could be enhanced with actual uptime
            })
        
        elif message_type == 'status':
            await self.send_message('status_response', {
                'user_authenticated': not self.user.is_anonymous,
                'user_email': self.user.email,
                'connection_active': True,
                'server_time': self.get_timestamp()
            })
        
        else:
            # Let parent handle unknown message types
            await super().handle_message(message_type, data)