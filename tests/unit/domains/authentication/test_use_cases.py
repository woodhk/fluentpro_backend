import pytest
from domains.authentication.use_cases.register_user import RegisterUserUseCase
from domains.authentication.dto.requests import SignupRequest
from domains.authentication.models.user import User
from core.exceptions import ConflictError, Auth0Error, ValidationError


class TestRegisterUserUseCase:
    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_user_repository, mock_auth_service):
        # Arrange
        use_case = RegisterUserUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )
        
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        # Mock the authenticate method to return tokens
        mock_auth_service.authenticate = lambda email, password: {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600
        }
        
        # Act
        response = await use_case.execute(request)
        
        # Assert
        assert response.user.email == request.email
        assert response.user.full_name == request.full_name
        assert response.tokens.access_token == "test-access-token"
        assert response.tokens.refresh_token == "test-refresh-token"
        assert len(mock_user_repository.users) == 1  # User was saved
    
    @pytest.mark.asyncio
    async def test_cannot_register_duplicate_email(self, mock_user_repository, mock_auth_service):
        # Arrange
        existing_user = User(
            email="existing@example.com",
            full_name="Existing User",
            auth0_id="auth0|123456"
        )
        await mock_user_repository.save(existing_user)
        
        use_case = RegisterUserUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )
        
        request = SignupRequest(
            email="existing@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        # Act & Assert
        with pytest.raises(ConflictError) as excinfo:
            await use_case.execute(request)
        
        assert "already exists" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_auth_service_failure_during_registration(self, mock_user_repository, mock_auth_service):
        # Arrange
        use_case = RegisterUserUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )
        
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )
        
        # Mock create_user to raise an exception
        mock_auth_service.create_user = lambda email, password, metadata: (_ for _ in ()).throw(
            Exception("Auth0 service unavailable")
        )
        
        # Act & Assert
        with pytest.raises(Auth0Error) as excinfo:
            await use_case.execute(request)
        
        assert "Failed to create user" in str(excinfo.value)
        assert len(mock_user_repository.users) == 0  # No user saved in DB
    
    @pytest.mark.asyncio
    async def test_validates_signup_request(self, mock_user_repository, mock_auth_service):
        # Arrange
        use_case = RegisterUserUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )
        
        # Act & Assert - Invalid email
        with pytest.raises(ValidationError):
            invalid_request = SignupRequest(
                email="invalid-email",
                password="SecurePass123!",
                full_name="Test User"
            )
        
        # Act & Assert - Short password
        with pytest.raises(ValidationError):
            invalid_request = SignupRequest(
                email="test@example.com",
                password="short",
                full_name="Test User"
            )
        
        # Act & Assert - Single name
        with pytest.raises(ValidationError):
            invalid_request = SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                full_name="SingleName"
            )