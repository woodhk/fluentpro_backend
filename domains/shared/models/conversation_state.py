"""
Conversation state models for AI interactions.
Defines the schema for managing conversation state across AI interactions.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Roles for conversation messages"""
    USER = "user"
    ASSISTANT = "assistant" 
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Status of a conversation"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class ConversationMessage(BaseModel):
    """
    Represents a single message in a conversation.
    
    This includes messages from users, AI assistants, and system messages.
    """
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the message was created")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used for this message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "message_id": "msg-123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "What are the best practices for async programming?",
                "timestamp": "2024-01-15T10:30:00Z",
                "tokens_used": 15,
                "metadata": {
                    "source": "web_ui",
                    "language": "en"
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return self.dict()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the message."""
        self.metadata[key] = value


class ConversationContext(BaseModel):
    """
    Context information for a conversation.
    
    This includes user preferences, conversation settings, and contextual data
    that should be maintained across the conversation.
    """
    
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User-specific preferences")
    conversation_settings: Dict[str, Any] = Field(default_factory=dict, description="Conversation-specific settings")
    domain_context: Dict[str, Any] = Field(default_factory=dict, description="Domain-specific context data")
    session_metadata: Dict[str, Any] = Field(default_factory=dict, description="Session-level metadata")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "user_preferences": {
                    "language": "en",
                    "response_style": "detailed",
                    "expertise_level": "intermediate"
                },
                "conversation_settings": {
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7
                },
                "domain_context": {
                    "topic": "programming",
                    "learning_path": "async_programming",
                    "current_skill_level": "beginner"
                },
                "session_metadata": {
                    "source": "onboarding",
                    "step": "role_selection"
                }
            }
        }
    
    def update_user_preference(self, key: str, value: Any) -> None:
        """Update a user preference."""
        self.user_preferences[key] = value
    
    def update_conversation_setting(self, key: str, value: Any) -> None:
        """Update a conversation setting."""
        self.conversation_settings[key] = value
    
    def update_domain_context(self, key: str, value: Any) -> None:
        """Update domain context."""
        self.domain_context[key] = value
    
    def get_context_for_ai(self) -> Dict[str, Any]:
        """Get context formatted for AI consumption."""
        return {
            "user_preferences": self.user_preferences,
            "domain_context": self.domain_context,
            "conversation_settings": self.conversation_settings
        }


class ConversationState(BaseModel):
    """
    Complete state of a conversation with an AI assistant.
    
    This is the main model that represents all the information needed
    to maintain context across multiple requests in a conversation.
    """
    
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique conversation identifier")
    user_id: str = Field(..., description="ID of the user participating in the conversation")
    session_id: Optional[str] = Field(None, description="Optional session ID for grouping conversations")
    
    # Conversation content
    messages: List[ConversationMessage] = Field(default_factory=list, description="List of messages in the conversation")
    context: ConversationContext = Field(default_factory=ConversationContext, description="Conversation context and settings")
    
    # Conversation state
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, description="Current status of the conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the conversation was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the conversation was last updated")
    last_activity_at: datetime = Field(default_factory=datetime.utcnow, description="When the last activity occurred")
    
    # Token tracking
    total_tokens_used: int = Field(default=0, description="Total tokens used in this conversation")
    token_limit: Optional[int] = Field(None, description="Optional token limit for this conversation")
    
    # Conversation metadata
    title: Optional[str] = Field(None, description="Optional title for the conversation")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the conversation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional conversation metadata")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-456",
                "session_id": "session-789",
                "messages": [],
                "context": {},
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "last_activity_at": "2024-01-15T10:35:00Z",
                "total_tokens_used": 150,
                "token_limit": 4000,
                "title": "Role Recommendation Discussion",
                "tags": ["onboarding", "career"],
                "metadata": {
                    "source": "web_ui",
                    "feature": "role_recommendations"
                }
            }
        }
    
    def add_message(self, message: ConversationMessage) -> None:
        """Add a new message to the conversation."""
        self.messages.append(message)
        self.update_activity()
        
        # Update token count if provided
        if message.tokens_used:
            self.total_tokens_used += message.tokens_used
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """Add a user message to the conversation."""
        message = ConversationMessage(
            role=MessageRole.USER,
            content=content,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_assistant_message(
        self, 
        content: str, 
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add an assistant message to the conversation."""
        message = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            tokens_used=tokens_used,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """Add a system message to the conversation."""
        message = ConversationMessage(
            role=MessageRole.SYSTEM,
            content=content,
            metadata=metadata or {}
        )
        self.add_message(message)
        return message
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_messages_for_ai(self, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get messages formatted for AI consumption.
        
        Args:
            max_messages: Optional limit on number of recent messages to include
            
        Returns:
            List of messages in AI-compatible format
        """
        messages = self.messages
        
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation context."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "message_count": len(self.messages),
            "total_tokens": self.total_tokens_used,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity_at.isoformat(),
            "context": self.context.get_context_for_ai()
        }
    
    def set_status(self, status: ConversationStatus) -> None:
        """Update the conversation status."""
        self.status = status
        self.update_activity()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the conversation."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the conversation."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def is_near_token_limit(self, threshold: float = 0.8) -> bool:
        """
        Check if conversation is near the token limit.
        
        Args:
            threshold: Percentage threshold (0.0 to 1.0)
            
        Returns:
            True if near token limit
        """
        if not self.token_limit:
            return False
        
        return self.total_tokens_used >= (self.token_limit * threshold)
    
    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if count < len(self.messages) else self.messages
    
    def clear_messages(self) -> None:
        """Clear all messages (useful for context window management)."""
        self.messages.clear()
        self.total_tokens_used = 0
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation state to dictionary representation."""
        return self.dict()


class ConversationStateDelta(BaseModel):
    """
    Represents changes to a conversation state.
    
    Used for efficient updates and event publishing.
    """
    
    conversation_id: str = Field(..., description="ID of the conversation being updated")
    operation: Literal["add_message", "update_context", "update_status", "update_metadata"] = Field(..., description="Type of operation")
    changes: Dict[str, Any] = Field(..., description="Changes being made")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the change was made")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }