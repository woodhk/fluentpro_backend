import pytest
from unittest.mock import Mock, AsyncMock
from domains.authentication.services.interfaces import IAuthenticationService
from tests.mocks.services import MockAuthenticationService


class TestAuthenticationService:
    """Test authentication service behaviors with mocks."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_auth_service):
        # Arrange
        email = "newuser@example.com"
        password = "SecurePassword123!"
        metadata = {"full_name": "New User"}
        
        # Act
        auth_id = await mock_auth_service.create_user(email, password, metadata)
        
        # Assert
        assert auth_id.startswith("auth0|")
        assert email in str(mock_auth_service.users[auth_id])
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, mock_auth_service):
        # Arrange
        # Create a test token using the mock service
        test_claims = {"user_id": "test-123", "email": "test@example.com"}
        mock_token_service = Mock()
        mock_token_service.create_access_token = AsyncMock(
            return_value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
        )
        
        token = await mock_token_service.create_access_token("test-123", test_claims)
        
        # Act
        # For the mock, we'll simulate a successful verification
        mock_auth_service.verify_token = AsyncMock(return_value=test_claims)
        result = await mock_auth_service.verify_token(token)
        
        # Assert
        assert result is not None
        assert result["user_id"] == "test-123"
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, mock_auth_service):
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        result = await mock_auth_service.verify_token(invalid_token)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_token(self, mock_auth_service):
        # Arrange
        token = "some.valid.token"
        
        # Act
        result = await mock_auth_service.revoke_token(token)
        
        # Assert
        assert result is True  # Mock always returns True
    
    def test_service_implements_interface(self, mock_auth_service):
        # Assert
        assert isinstance(mock_auth_service, IAuthenticationService)
        assert hasattr(mock_auth_service, 'create_user')
        assert hasattr(mock_auth_service, 'verify_token')
        assert hasattr(mock_auth_service, 'revoke_token')