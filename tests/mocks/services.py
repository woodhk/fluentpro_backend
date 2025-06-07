from domains.authentication.services.interfaces import IAuthenticationService, ITokenService
from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
from typing import Optional, Dict, Any, List
import uuid
import jwt

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