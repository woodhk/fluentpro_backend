"""
Shared domain models used across multiple domains.
"""

from .base_entity import BaseEntity
from .conversation_state import (
    ConversationMessage,
    ConversationContext,
    ConversationState,
    ConversationStateDelta,
    MessageRole,
    ConversationStatus
)

__all__ = [
    'BaseEntity',
    'ConversationMessage',
    'ConversationContext', 
    'ConversationState',
    'ConversationStateDelta',
    'MessageRole',
    'ConversationStatus',
]