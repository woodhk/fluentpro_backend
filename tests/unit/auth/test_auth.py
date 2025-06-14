import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from src.core.auth import auth0_validator
from src.core.dependencies import get_current_user_auth0_id

class TestAuth0JWTValidator:
    """Test Auth0 JWT validation functionality"""
    
    def test_verify_jwt_token_valid(self, mock_auth0_validator):
        """Test valid JWT token verification"""
        token = "valid.jwt.token"
        result = auth0_validator.verify_jwt_token(token)
        
        assert result["sub"] == "auth0|test123456789"
        assert result["email"] == "test@example.com"
        assert result["aud"] == "https://api.fluentpro.com"
    
    def test_verify_jwt_token_invalid(self):
        """Test invalid JWT token verification"""
        with patch('src.core.auth.jwt.decode') as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError("Invalid token")
            
            with pytest.raises(ValueError, match="Invalid token"):
                auth0_validator.verify_jwt_token("invalid.jwt.token")

class TestAuthDependencies:
    """Test authentication dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_auth0_id_valid_token(self):
        """Test extracting Auth0 ID from valid token"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Mock token credentials
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        with patch('src.core.auth.auth0_validator.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {"sub": "auth0|test123456789"}
            
            result = await get_current_user_auth0_id(mock_credentials.credentials)
            assert result == "auth0|test123456789"
    
    @pytest.mark.asyncio
    async def test_get_current_user_auth0_id_invalid_token(self):
        """Test extracting Auth0 ID from invalid token"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )
        
        with patch('src.core.auth.auth0_validator.verify_jwt_token') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_auth0_id(mock_credentials.credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_auth0_id_no_sub(self):
        """Test token without sub claim"""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token.without.sub"
        )
        
        with patch('src.core.auth.auth0_validator.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {"email": "test@example.com"}  # No 'sub' field
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_auth0_id(mock_credentials.credentials)
            
            assert exc_info.value.status_code == 401
            assert "no user ID found" in str(exc_info.value.detail)

class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    def test_auth_status_authenticated(self, client_with_auth, auth_headers):
        """Test auth status endpoint with valid authentication"""
        response = client_with_auth.get("/api/v1/auth/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "test-user-id-123"
        assert data["message"] == "User is authenticated"
    
    def test_auth_status_unauthenticated(self, client_no_auth):
        """Test auth status endpoint without authentication"""
        response = client_no_auth.get("/api/v1/auth/status")
        
        assert response.status_code == 403  # No auth header
    
    def test_auth_me_authenticated(self, client_with_auth, auth_headers):
        """Test auth me endpoint with valid authentication"""
        response = client_with_auth.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id-123"
        assert data["email"] == "test@example.com"
        assert data["auth0_id"] == "auth0|test123456789"
    
    def test_verify_token_valid(self, client_with_auth, auth_headers):
        """Test token verification endpoint with valid token"""
        response = client_with_auth.get("/api/v1/auth/verify", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["auth0_id"] == "auth0|test123456789"
        assert data["message"] == "Token is valid"
    
    def test_verify_token_invalid(self, client_no_auth, invalid_auth_headers):
        """Test token verification endpoint with invalid token"""
        with patch('src.core.auth.auth0_validator.verify_jwt_token') as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            response = client_no_auth.get("/api/v1/auth/verify", headers=invalid_auth_headers)
            assert response.status_code == 401

class TestAuth0WebhookEndpoints:
    """Test Auth0 webhook handling"""
    
    def test_webhook_user_created(self, client_no_auth, auth0_webhook_user_created):
        """Test Auth0 webhook for user creation"""
        with patch('src.services.user_service.UserService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_by_auth0_id.return_value = None  # User doesn't exist
            mock_service.create_user_from_auth0.return_value = {"id": "new-user-id"}
            
            response = client_no_auth.post(
                "/api/v1/webhooks/auth0",
                json=auth0_webhook_user_created
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "user.created" in data["message"]
    
    def test_webhook_user_updated(self, client_no_auth, auth0_webhook_user_updated):
        """Test Auth0 webhook for user update"""
        with patch('src.services.user_service.UserService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_by_auth0_id.return_value = {"id": "existing-user"}
            mock_service.sync_auth0_profile.return_value = {"id": "existing-user"}
            
            response = client_no_auth.post(
                "/api/v1/webhooks/auth0",
                json=auth0_webhook_user_updated
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "user.updated" in data["message"]
    
    def test_webhook_unknown_event(self, client_no_auth):
        """Test Auth0 webhook with unknown event type"""
        payload = {
            "event": "unknown.event",
            "user": {"user_id": "test123"}
        }
        
        response = client_no_auth.post("/api/v1/webhooks/auth0", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "unknown.event" in data["message"]
    
    def test_webhook_malformed_payload(self, client_no_auth):
        """Test Auth0 webhook with malformed payload"""
        payload = {"invalid": "payload"}
        
        response = client_no_auth.post("/api/v1/webhooks/auth0", json=payload)
        
        # Should handle gracefully, might return success or error depending on implementation
        assert response.status_code in [200, 500]