from domains.authentication.services.interfaces import IAuthenticationService, ITokenService
from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
from infrastructure.messaging.event_bus import IEventBus
from infrastructure.persistence.cache.cache_manager import ICacheManager
from infrastructure.persistence.cache.session_store import ISessionStore, SessionData
from domains.shared.events.base_event import DomainEvent
from domains.shared.models.conversation_state import ConversationState
from typing import Optional, Dict, Any, List, Type, Callable, Awaitable, Union
from datetime import datetime, timedelta
import uuid
import jwt
import asyncio

class MockAuthenticationService(IAuthenticationService):
    def __init__(self):
        self.users = {}
    
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        auth_id = f"auth0|{uuid.uuid4()}"
        self.users[auth_id] = {
            "email": email,
            "metadata": metadata
        }
        return auth_id
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            # Simple decode for testing
            return jwt.decode(token, "test-secret", algorithms=["HS256"])
        except:
            return None
    
    async def revoke_token(self, token: str) -> bool:
        # Mock implementation always succeeds
        return True

class MockTokenService(ITokenService):
    async def create_access_token(self, user_id: str, claims: Dict[str, Any]) -> str:
        # Create test token
        payload = {"user_id": user_id, **claims}
        return jwt.encode(payload, "test-secret", algorithm="HS256")
    
    async def create_refresh_token(self, user_id: str) -> str:
        # Create test refresh token
        payload = {"user_id": user_id, "type": "refresh"}
        return jwt.encode(payload, "test-secret", algorithm="HS256")

class MockEmbeddingService(IEmbeddingService):
    async def create_embedding(self, text: str) -> List[float]:
        # Return deterministic embedding based on text length
        return [0.1 * i for i in range(1536)]  # Simulate OpenAI embedding size
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [await self.create_embedding(text) for text in texts]

class MockCompletionService(ICompletionService):
    async def complete(self, prompt: str, max_tokens: int = 100) -> str:
        # Return predictable response for testing
        return f"Mock response to: {prompt[:50]}..."
    
    async def complete_with_system(self, system: str, user: str, max_tokens: int = 100) -> str:
        # Return predictable response with system context
        return f"Mock response with system '{system[:20]}...' to user: {user[:30]}..."


class MockEventBus(IEventBus):
    """Mock event bus for testing"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self._published_events: List[DomainEvent] = []
    
    async def publish(self, event: DomainEvent) -> None:
        """Mock publish - stores events for verification"""
        self._published_events.append(event)
        
        # Call handlers if any are registered
        handlers = self._handlers.get(event.event_type, [])
        if handlers:
            tasks = [handler(event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], Awaitable[None]]) -> None:
        """Mock subscribe - registers handlers"""
        # Get event type string from the class
        event_type_str = getattr(event_type, 'event_type', event_type.__name__)
        if event_type_str not in self._handlers:
            self._handlers[event_type_str] = []
        self._handlers[event_type_str].append(handler)
    
    def get_published_events(self) -> List[DomainEvent]:
        """Test helper to get published events"""
        return self._published_events.copy()
    
    def clear_events(self) -> None:
        """Test helper to clear published events"""
        self._published_events.clear()


class MockCacheManager(ICacheManager):
    """Mock cache manager for testing"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ttls: Dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Mock get - returns value if not expired"""
        if key not in self._cache:
            return None
        
        # Check TTL
        if key in self._ttls and datetime.utcnow() > self._ttls[key]:
            del self._cache[key]
            del self._ttls[key]
            return None
        
        return self._cache[key]
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Mock set - stores value with optional TTL"""
        self._cache[key] = value
        
        if ttl is not None:
            if isinstance(ttl, int):
                expire_time = datetime.utcnow() + timedelta(seconds=ttl)
            else:
                expire_time = datetime.utcnow() + ttl
            self._ttls[key] = expire_time
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Mock delete - removes key"""
        if key in self._cache:
            del self._cache[key]
            if key in self._ttls:
                del self._ttls[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Mock exists - checks if key exists and not expired"""
        value = await self.get(key)
        return value is not None
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Mock set_many - stores multiple values"""
        for key, value in mapping.items():
            await self.set(key, value, ttl)
        return True
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Mock get_many - gets multiple values"""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def clear_cache(self) -> None:
        """Test helper to clear cache"""
        self._cache.clear()
        self._ttls.clear()


class MockSessionStore(ISessionStore):
    """Mock session store for testing"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Mock create_session - creates and stores session"""
        session_id = str(uuid.uuid4())
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            data=session_data,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self._sessions[session_id] = session
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Mock get_session - returns session if not expired"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        if datetime.utcnow() > session.expires_at:
            del self._sessions[session_id]
            return None
        
        # Update last accessed
        session.last_accessed = datetime.utcnow()
        return session
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Mock update_session - updates session data"""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        if datetime.utcnow() > session.expires_at:
            del self._sessions[session_id]
            return False
        
        session.data.update(session_data)
        session.last_accessed = datetime.utcnow()
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Mock delete_session - removes session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def extend_session(self, session_id: str, extension: timedelta) -> bool:
        """Mock extend_session - extends session expiry"""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        session.expires_at += extension
        session.last_accessed = datetime.utcnow()
        return True
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Mock get_user_sessions - returns all sessions for user"""
        return [
            session for session in self._sessions.values()
            if session.user_id == user_id and datetime.utcnow() <= session.expires_at
        ]
    
    def clear_sessions(self) -> None:
        """Test helper to clear all sessions"""
        self._sessions.clear()


class MockConversationStateManager:
    """Mock conversation state manager for testing"""
    
    def __init__(self):
        self._conversations: Dict[str, ConversationState] = {}
    
    async def create_conversation(
        self,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """Mock create_conversation - creates new conversation state"""
        conversation_id = str(uuid.uuid4())
        conversation = ConversationState(
            conversation_id=conversation_id,
            user_id=user_id,
            status='active',
            context=initial_context or {},
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self._conversations[conversation_id] = conversation
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Mock get_conversation - returns conversation if exists"""
        return self._conversations.get(conversation_id)
    
    async def update_conversation(
        self,
        conversation_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ConversationState]:
        """Mock update_conversation - updates conversation state"""
        if conversation_id not in self._conversations:
            return None
        
        conversation = self._conversations[conversation_id]
        for key, value in updates.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)
        
        conversation.updated_at = datetime.utcnow()
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Mock delete_conversation - removes conversation"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    async def get_user_conversations(self, user_id: str) -> List[ConversationState]:
        """Mock get_user_conversations - returns all conversations for user"""
        return [
            conv for conv in self._conversations.values()
            if conv.user_id == user_id
        ]
    
    def clear_conversations(self) -> None:
        """Test helper to clear all conversations"""
        self._conversations.clear()