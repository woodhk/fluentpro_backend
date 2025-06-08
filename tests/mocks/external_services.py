"""
Mock implementations for external services used in testing.
"""

import uuid
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Mock OpenAI Client
class IOpenAIClient(ABC):
    """Interface for OpenAI client"""
    
    @abstractmethod
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        pass
    
    @abstractmethod
    async def create_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        pass


class MockOpenAIClient(IOpenAIClient):
    """Mock OpenAI client for testing"""
    
    def __init__(self):
        self.request_count = 0
        self.embeddings_created = []
        self.completions_created = []
        self.should_fail = False
        self.failure_message = "Mock OpenAI service failure"
    
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Create mock embedding vector"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        # Create deterministic embedding based on text
        embedding = [0.1 * (i + 1) * len(text) % 100 / 100 for i in range(1536)]
        
        self.embeddings_created.append({
            'text': text,
            'model': model,
            'embedding': embedding,
            'timestamp': datetime.utcnow()
        })
        
        return embedding
    
    async def create_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Create mock completion response"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        # Generate mock response based on last message
        last_message = messages[-1] if messages else {"content": ""}
        response_text = f"Mock AI response to: {last_message.get('content', '')[:50]}..."
        
        response = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg.get("content", "")) for msg in messages) // 4,
                "completion_tokens": len(response_text) // 4,
                "total_tokens": (sum(len(msg.get("content", "")) for msg in messages) + len(response_text)) // 4
            }
        }
        
        self.completions_created.append({
            'messages': messages,
            'response': response,
            'model': model,
            'timestamp': datetime.utcnow()
        })
        
        return response
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock OpenAI service failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_request_count(self) -> int:
        """Get total number of requests made"""
        return self.request_count
    
    def clear_history(self):
        """Clear request history"""
        self.request_count = 0
        self.embeddings_created.clear()
        self.completions_created.clear()


# Mock Auth0 Client
class IAuth0Client(ABC):
    """Interface for Auth0 client"""
    
    @abstractmethod
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        pass


class MockAuth0Client(IAuth0Client):
    """Mock Auth0 client for testing"""
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.request_count = 0
        self.should_fail = False
        self.failure_message = "Mock Auth0 service failure"
    
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        """Create mock user in Auth0"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        user_id = f"auth0|{uuid.uuid4()}"
        user_data = {
            "user_id": user_id,
            "email": email,
            "email_verified": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "app_metadata": metadata.get("app_metadata", {}),
            "user_metadata": metadata.get("user_metadata", {}),
            "blocked": False,
            "last_login": None,
            "logins_count": 0
        }
        
        self.users[user_id] = user_data
        return user_id
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from Auth0"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        return self.users.get(user_id)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user in Auth0"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        user.update(updates)
        user["updated_at"] = datetime.utcnow().isoformat()
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Auth0"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        # Mock token verification - in real implementation would validate JWT
        if token in self.tokens:
            token_data = self.tokens[token]
            if datetime.fromisoformat(token_data["expires_at"]) > datetime.utcnow():
                return token_data["payload"]
        
        # Return mock payload for test tokens
        if token.startswith("test_token_"):
            return {
                "sub": f"auth0|{uuid.uuid4()}",
                "email": "test@example.com",
                "email_verified": True,
                "iat": int(datetime.utcnow().timestamp()),
                "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            }
        
        return None
    
    def create_test_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """Create a test token for testing"""
        token = f"test_token_{uuid.uuid4()}"
        payload = {
            "sub": user_id,
            "email": "test@example.com",
            "email_verified": True,
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=expires_in_hours)).timestamp())
        }
        
        self.tokens[token] = {
            "payload": payload,
            "expires_at": (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat()
        }
        
        return token
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock Auth0 service failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_request_count(self) -> int:
        """Get total number of requests made"""
        return self.request_count
    
    def clear_data(self):
        """Clear all mock data"""
        self.users.clear()
        self.tokens.clear()
        self.request_count = 0


# Mock Azure Client
class IAzureClient(ABC):
    """Interface for Azure services client"""
    
    @abstractmethod
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def index_document(self, document_id: str, content: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        pass


class MockAzureClient(IAzureClient):
    """Mock Azure client for testing"""
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.request_count = 0
        self.should_fail = False
        self.failure_message = "Mock Azure service failure"
    
    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search documents in Azure Search"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        # Simple mock search - return documents that contain query terms
        results = []
        query_lower = query.lower()
        
        for doc_id, document in self.documents.items():
            content = str(document.get("content", "")).lower()
            if query_lower in content:
                results.append({
                    "id": doc_id,
                    "score": 0.8,  # Mock relevance score
                    **document
                })
        
        return results[:10]  # Return top 10 results
    
    async def index_document(self, document_id: str, content: Dict[str, Any]) -> bool:
        """Index document in Azure Search"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.documents[document_id] = {
            **content,
            "indexed_at": datetime.utcnow().isoformat()
        }
        return True
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from Azure Search"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock Azure service failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_request_count(self) -> int:
        """Get total number of requests made"""
        return self.request_count
    
    def clear_data(self):
        """Clear all mock data"""
        self.documents.clear()
        self.request_count = 0


# Mock Redis Client
class MockRedisClient:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expires: Dict[str, datetime] = {}
        self.request_count = 0
        self.should_fail = False
        self.failure_message = "Mock Redis service failure"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if key not in self._data:
            return None
        
        # Check expiration
        if key in self._expires and datetime.utcnow() > self._expires[key]:
            del self._data[key]
            del self._expires[key]
            return None
        
        return self._data[key]
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self._data[key] = value
        
        if ex is not None:
            self._expires[key] = datetime.utcnow() + timedelta(seconds=ex)
        
        return True
    
    async def delete(self, key: str) -> int:
        """Delete key from Redis"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if key in self._data:
            del self._data[key]
            if key in self._expires:
                del self._expires[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        """Check if key exists"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        value = await self.get(key)
        return 1 if value is not None else 0
    
    async def expire(self, key: str, seconds: int) -> int:
        """Set expiration on key"""
        self.request_count += 1
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        if key in self._data:
            self._expires[key] = datetime.utcnow() + timedelta(seconds=seconds)
            return 1
        return 0
    
    def set_failure_mode(self, should_fail: bool, message: str = "Mock Redis service failure"):
        """Configure mock to simulate failures"""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_request_count(self) -> int:
        """Get total number of requests made"""
        return self.request_count
    
    def clear_data(self):
        """Clear all mock data"""
        self._data.clear()
        self._expires.clear()
        self.request_count = 0


# Factory functions for creating mock services
def create_mock_external_services() -> Dict[str, Any]:
    """Create all mock external services for testing"""
    return {
        'openai_client': MockOpenAIClient(),
        'auth0_client': MockAuth0Client(),
        'azure_client': MockAzureClient(),
        'redis_client': MockRedisClient()
    }


def create_failing_external_services(failure_message: str = "Service unavailable") -> Dict[str, Any]:
    """Create mock external services configured to fail"""
    services = create_mock_external_services()
    
    for service in services.values():
        if hasattr(service, 'set_failure_mode'):
            service.set_failure_mode(True, failure_message)
    
    return services