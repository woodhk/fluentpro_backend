"""
Conversation state manager for AI interactions.

Provides persistence and management of conversation state across AI interactions,
enabling context maintenance and session recovery.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
import uuid

from domains.shared.models.conversation_state import (
    ConversationState,
    ConversationMessage,
    ConversationContext,
    ConversationStatus,
    MessageRole,
    ConversationStateDelta
)
from infrastructure.persistence.cache.session_store import ISessionStore, SessionData
from domains.shared.events.base_event import DomainEvent

logger = logging.getLogger(__name__)


class ConversationStateEvent(DomainEvent):
    """Event published when conversation state changes"""
    
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        operation: str,
        changes: Dict[str, Any],
        **kwargs
    ):
        super().__init__(
            aggregate_id=conversation_id,
            event_type="conversation.state_changed",
            **kwargs
        )
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.operation = operation
        self.changes = changes


class IConversationStateManager(ABC):
    """Interface for conversation state management"""
    
    @abstractmethod
    async def create_conversation(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        ttl_seconds: int = 86400  # 24 hours default
    ) -> ConversationState:
        """Create a new conversation"""
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation by ID"""
        pass
    
    @abstractmethod
    async def update_conversation(
        self,
        conversation_id: str,
        updates: ConversationStateDelta
    ) -> bool:
        """Update conversation with delta changes"""
        pass
    
    @abstractmethod
    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage
    ) -> bool:
        """Add a message to the conversation"""
        pass
    
    @abstractmethod
    async def get_user_conversations(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 50
    ) -> List[ConversationState]:
        """Get conversations for a user"""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        pass
    
    @abstractmethod
    async def extend_conversation_ttl(
        self,
        conversation_id: str,
        ttl_seconds: int = 86400
    ) -> bool:
        """Extend conversation TTL"""
        pass
    
    @abstractmethod
    async def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations"""
        pass


class RedisConversationStateManager(IConversationStateManager):
    """Redis-backed conversation state manager"""
    
    def __init__(
        self,
        session_store: ISessionStore,
        event_bus: Optional[Any] = None,
        key_prefix: str = "conversation:",
        user_conversations_prefix: str = "user_conversations:"
    ):
        """
        Initialize conversation state manager
        
        Args:
            session_store: Session store for persistence
            event_bus: Optional event bus for publishing state changes
            key_prefix: Prefix for conversation keys
            user_conversations_prefix: Prefix for user conversation tracking
        """
        self.session_store = session_store
        self.event_bus = event_bus
        self.key_prefix = key_prefix
        self.user_conversations_prefix = user_conversations_prefix
    
    def _get_conversation_key(self, conversation_id: str) -> str:
        """Get Redis key for conversation"""
        return f"{self.key_prefix}{conversation_id}"
    
    def _get_user_conversations_key(self, user_id: str) -> str:
        """Get Redis key for user conversations tracking"""
        return f"{self.user_conversations_prefix}{user_id}"
    
    async def create_conversation(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        ttl_seconds: int = 86400
    ) -> ConversationState:
        """Create a new conversation"""
        try:
            conversation = ConversationState(
                user_id=user_id,
                session_id=session_id,
                context=context or ConversationContext()
            )
            
            # Store conversation using session store
            conversation_key = self._get_conversation_key(conversation.conversation_id)
            conversation_data = conversation.dict()
            
            await self.session_store.create_session(
                session_id=conversation_key,
                user_id=user_id,
                data=conversation_data,
                ttl_seconds=ttl_seconds
            )
            
            # Track conversation for user
            await self._add_to_user_conversations(user_id, conversation.conversation_id)
            
            # Publish event if event bus available
            if self.event_bus:
                event = ConversationStateEvent(
                    conversation_id=conversation.conversation_id,
                    user_id=user_id,
                    operation="create",
                    changes={"status": conversation.status.value}
                )
                await self.event_bus.publish(event)
            
            logger.info(f"Created conversation {conversation.conversation_id} for user {user_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation for user {user_id}: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation by ID"""
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            session_data = await self.session_store.get_session(conversation_key)
            
            if not session_data:
                return None
            
            # Reconstruct conversation state from session data
            conversation_dict = session_data.data
            conversation = ConversationState.parse_obj(conversation_dict)
            
            logger.debug(f"Retrieved conversation {conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    async def update_conversation(
        self,
        conversation_id: str,
        updates: ConversationStateDelta
    ) -> bool:
        """Update conversation with delta changes"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for update")
                return False
            
            # Apply updates based on operation type
            if updates.operation == "add_message":
                message_data = updates.changes.get("message")
                if message_data:
                    message = ConversationMessage.parse_obj(message_data)
                    conversation.add_message(message)
            
            elif updates.operation == "update_context":
                context_updates = updates.changes.get("context", {})
                for key, value in context_updates.items():
                    if hasattr(conversation.context, key):
                        setattr(conversation.context, key, value)
                conversation.update_activity()
            
            elif updates.operation == "update_status":
                new_status = updates.changes.get("status")
                if new_status:
                    conversation.set_status(ConversationStatus(new_status))
            
            elif updates.operation == "update_metadata":
                metadata_updates = updates.changes.get("metadata", {})
                conversation.metadata.update(metadata_updates)
                conversation.update_activity()
            
            # Save updated conversation
            conversation_key = self._get_conversation_key(conversation_id)
            update_result = await self.session_store.update_session(
                session_id=conversation_key,
                data=conversation.dict(),
                extend_ttl=True
            )
            
            # Publish event if event bus available
            if self.event_bus and update_result:
                event = ConversationStateEvent(
                    conversation_id=conversation_id,
                    user_id=conversation.user_id,
                    operation=updates.operation,
                    changes=updates.changes
                )
                await self.event_bus.publish(event)
            
            logger.debug(f"Updated conversation {conversation_id} with operation {updates.operation}")
            return update_result
            
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            return False
    
    async def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage
    ) -> bool:
        """Add a message to the conversation"""
        try:
            updates = ConversationStateDelta(
                conversation_id=conversation_id,
                operation="add_message",
                changes={"message": message.dict()}
            )
            
            return await self.update_conversation(conversation_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return False
    
    async def get_user_conversations(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 50
    ) -> List[ConversationState]:
        """Get conversations for a user"""
        try:
            # Get user's conversation sessions
            user_sessions = await self.session_store.get_user_sessions(user_id)
            
            conversations = []
            conversation_count = 0
            
            for session in user_sessions:
                if conversation_count >= limit:
                    break
                
                # Check if this is a conversation session
                if session.session_id.startswith(self.key_prefix):
                    try:
                        conversation = ConversationState.parse_obj(session.data)
                        
                        # Filter by status if specified
                        if status is None or conversation.status == status:
                            conversations.append(conversation)
                            conversation_count += 1
                    
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation from session {session.session_id}: {e}")
                        continue
            
            # Sort by last activity (most recent first)
            conversations.sort(key=lambda c: c.last_activity_at, reverse=True)
            
            logger.debug(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        try:
            # Get conversation first to get user_id
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            # Delete conversation session
            conversation_key = self._get_conversation_key(conversation_id)
            delete_result = await self.session_store.delete_session(conversation_key)
            
            # Remove from user conversations tracking
            if delete_result:
                await self._remove_from_user_conversations(conversation.user_id, conversation_id)
                
                # Publish event if event bus available
                if self.event_bus:
                    event = ConversationStateEvent(
                        conversation_id=conversation_id,
                        user_id=conversation.user_id,
                        operation="delete",
                        changes={}
                    )
                    await self.event_bus.publish(event)
            
            logger.info(f"Deleted conversation {conversation_id}")
            return delete_result
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    async def extend_conversation_ttl(
        self,
        conversation_id: str,
        ttl_seconds: int = 86400
    ) -> bool:
        """Extend conversation TTL"""
        try:
            conversation_key = self._get_conversation_key(conversation_id)
            result = await self.session_store.extend_session_ttl(conversation_key, ttl_seconds)
            
            if result:
                logger.debug(f"Extended TTL for conversation {conversation_id} by {ttl_seconds}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extend TTL for conversation {conversation_id}: {e}")
            return False
    
    async def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations"""
        try:
            # Use session store cleanup functionality
            cleanup_count = await self.session_store.cleanup_expired_sessions()
            
            logger.info(f"Cleaned up {cleanup_count} expired conversations")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired conversations: {e}")
            return 0
    
    async def _add_to_user_conversations(self, user_id: str, conversation_id: str) -> None:
        """Add conversation to user's conversation tracking"""
        try:
            # This would use Redis sets or similar to track user conversations
            # For now, we rely on the session store's user session tracking
            pass
        except Exception as e:
            logger.warning(f"Failed to add conversation {conversation_id} to user {user_id} tracking: {e}")
    
    async def _remove_from_user_conversations(self, user_id: str, conversation_id: str) -> None:
        """Remove conversation from user's conversation tracking"""
        try:
            # This would remove from Redis sets or similar
            # For now, we rely on the session store's cleanup
            pass
        except Exception as e:
            logger.warning(f"Failed to remove conversation {conversation_id} from user {user_id} tracking: {e}")


class ConversationContextManager:
    """
    Manages conversation context and provides utilities for context window management.
    
    This class provides higher-level operations for managing conversation context,
    including context window management for AI models with token limits.
    """
    
    def __init__(self, state_manager: IConversationStateManager):
        """
        Initialize context manager
        
        Args:
            state_manager: Conversation state manager instance
        """
        self.state_manager = state_manager
    
    async def add_user_message(
        self,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a user message to the conversation"""
        try:
            message = ConversationMessage(
                role=MessageRole.USER,
                content=content,
                metadata=metadata or {}
            )
            
            return await self.state_manager.add_message(conversation_id, message)
            
        except Exception as e:
            logger.error(f"Failed to add user message to conversation {conversation_id}: {e}")
            return False
    
    async def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add an assistant message to the conversation"""
        try:
            message = ConversationMessage(
                role=MessageRole.ASSISTANT,
                content=content,
                tokens_used=tokens_used,
                metadata=metadata or {}
            )
            
            return await self.state_manager.add_message(conversation_id, message)
            
        except Exception as e:
            logger.error(f"Failed to add assistant message to conversation {conversation_id}: {e}")
            return False
    
    async def get_context_for_ai(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation context formatted for AI consumption
        
        Args:
            conversation_id: ID of the conversation
            max_messages: Maximum number of recent messages to include
            max_tokens: Maximum token count (for context window management)
            
        Returns:
            Context dictionary suitable for AI APIs
        """
        try:
            conversation = await self.state_manager.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Get messages with optional limits
            messages = conversation.get_messages_for_ai(max_messages)
            
            # Apply token limit if specified (rough estimation)
            if max_tokens and conversation.total_tokens_used > max_tokens:
                # Truncate messages from the beginning, keeping most recent
                estimated_tokens_per_message = conversation.total_tokens_used // len(conversation.messages) if conversation.messages else 0
                if estimated_tokens_per_message > 0:
                    max_messages_for_tokens = max_tokens // estimated_tokens_per_message
                    messages = messages[-max_messages_for_tokens:] if max_messages_for_tokens > 0 else []
            
            return {
                "messages": messages,
                "context": conversation.context.get_context_for_ai(),
                "conversation_summary": conversation.get_context_summary()
            }
            
        except Exception as e:
            logger.error(f"Failed to get AI context for conversation {conversation_id}: {e}")
            return None
    
    async def update_context(
        self,
        conversation_id: str,
        context_updates: Dict[str, Any]
    ) -> bool:
        """Update conversation context"""
        try:
            updates = ConversationStateDelta(
                conversation_id=conversation_id,
                operation="update_context",
                changes={"context": context_updates}
            )
            
            return await self.state_manager.update_conversation(conversation_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update context for conversation {conversation_id}: {e}")
            return False
    
    async def manage_context_window(
        self,
        conversation_id: str,
        token_limit: int,
        preserve_recent_messages: int = 5
    ) -> bool:
        """
        Manage conversation context window by trimming old messages
        
        Args:
            conversation_id: ID of the conversation
            token_limit: Maximum tokens to maintain
            preserve_recent_messages: Number of recent messages to always keep
            
        Returns:
            True if context window was managed successfully
        """
        try:
            conversation = await self.state_manager.get_conversation(conversation_id)
            if not conversation:
                return False
            
            # Check if we need to trim
            if conversation.total_tokens_used <= token_limit:
                return True
            
            # Keep recent messages and trim older ones
            messages_to_keep = conversation.get_recent_messages(preserve_recent_messages)
            
            # Calculate tokens for kept messages (rough estimation)
            estimated_tokens = sum(msg.tokens_used or 50 for msg in messages_to_keep)
            
            # Create new conversation state with trimmed messages
            conversation.messages = messages_to_keep
            conversation.total_tokens_used = estimated_tokens
            conversation.update_activity()
            
            # Update in storage
            conversation_key = self.state_manager._get_conversation_key(conversation_id)
            update_result = await self.state_manager.session_store.update_session(
                session_id=conversation_key,
                data=conversation.dict(),
                extend_ttl=True
            )
            
            logger.info(f"Managed context window for conversation {conversation_id}, kept {len(messages_to_keep)} messages")
            return update_result
            
        except Exception as e:
            logger.error(f"Failed to manage context window for conversation {conversation_id}: {e}")
            return False


class ConversationStateManagerFactory:
    """Factory for creating conversation state manager instances"""
    
    @staticmethod
    def create_redis_manager(
        session_store: ISessionStore,
        event_bus: Optional[Any] = None
    ) -> RedisConversationStateManager:
        """Create Redis-backed conversation state manager"""
        return RedisConversationStateManager(session_store, event_bus)
    
    @staticmethod
    def create_context_manager(
        state_manager: IConversationStateManager
    ) -> ConversationContextManager:
        """Create conversation context manager"""
        return ConversationContextManager(state_manager)