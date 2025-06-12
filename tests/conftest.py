import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from src.main import app
from src.core.dependencies import get_db, get_current_user
from src.integrations.supabase import SupabaseUserRepository

# Test data
MOCK_USER_DATA = {
    "id": "test-user-id-123",
    "auth0_id": "auth0|test123456789",
    "email": "test@example.com",
    "full_name": "Test User",
    "date_of_birth": "1990-01-01",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}

MOCK_AUTH0_TOKEN_PAYLOAD = {
    "sub": "auth0|test123456789",
    "email": "test@example.com",
    "name": "Test User",
    "email_verified": True,
    "iss": "https://dev-47g5ypdrz64lekwg.us.auth0.com/",
    "aud": "https://api.fluentpro.com",
    "iat": 1640995200,
    "exp": 1641081600
}

# Mock Supabase client
class MockSupabaseClient:
    def __init__(self):
        self.table_mock = Mock()
        
    def table(self, table_name: str):
        return self.table_mock

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    return MockSupabaseClient()

@pytest.fixture
def mock_user_repo(mock_supabase_client):
    """Mock user repository"""
    repo = SupabaseUserRepository(mock_supabase_client)
    repo.get_user_by_auth0_id = AsyncMock(return_value=MOCK_USER_DATA)
    repo.get_user_by_id = AsyncMock(return_value=MOCK_USER_DATA)
    repo.create_user = AsyncMock(return_value=MOCK_USER_DATA)
    repo.update_user = AsyncMock(return_value=MOCK_USER_DATA)
    return repo

@pytest.fixture
def mock_auth0_validator():
    """Mock Auth0 JWT validator"""
    with patch('src.core.auth.auth0_validator') as mock_validator:
        mock_validator.verify_jwt_token.return_value = MOCK_AUTH0_TOKEN_PAYLOAD
        yield mock_validator

@pytest.fixture
def client_with_auth(mock_supabase_client, mock_auth0_validator):
    """Test client with mocked authentication"""
    
    # Mock the database dependency
    async def mock_get_db():
        return mock_supabase_client
    
    # Mock the current user dependency
    async def mock_get_current_user():
        return MOCK_USER_DATA
    
    # Override dependencies
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with TestClient(app) as client:
        yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()

@pytest.fixture
def client_no_auth():
    """Test client without authentication"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers():
    """Valid authentication headers"""
    return {
        "Authorization": "Bearer valid-jwt-token"
    }

@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers"""
    return {
        "Authorization": "Bearer invalid-jwt-token"
    }

@pytest.fixture
def user_update_data():
    """Sample user update data"""
    return {
        "full_name": "Updated Test User",
        "date_of_birth": "1990-05-15"
    }

@pytest.fixture
def auth0_webhook_user_created():
    """Sample Auth0 webhook payload for user creation"""
    return {
        "event": "user.created",
        "user": {
            "user_id": "auth0|test123456789",
            "email": "newuser@example.com",
            "name": "New Test User",
            "email_verified": True
        }
    }

@pytest.fixture
def auth0_webhook_user_updated():
    """Sample Auth0 webhook payload for user update"""
    return {
        "event": "user.updated",
        "user": {
            "user_id": "auth0|test123456789",
            "email": "updated@example.com",
            "name": "Updated Test User",
            "email_verified": True
        }
    }

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()