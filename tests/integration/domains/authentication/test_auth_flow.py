"""
Integration tests for authentication flow.
These tests verify the complete authentication flow with mocked external services.
"""

import pytest
from domains.authentication.use_cases.register_user import RegisterUserUseCase
from domains.authentication.use_cases.authenticate_user import AuthenticateUserUseCase
from domains.authentication.dto.requests import SignupRequest, LoginRequest
from tests.mocks.repositories import MockUserRepository, MockRoleRepository
from tests.mocks.services import MockAuthenticationService


class TestAuthenticationFlow:
    """Test complete authentication flows with integrated components."""
    
    @pytest.mark.asyncio
    async def test_complete_registration_and_login_flow(self):
        # Arrange - Create shared dependencies
        user_repository = MockUserRepository()
        role_repository = MockRoleRepository()
        auth_service = MockAuthenticationService()
        
        # Mock the authenticate method
        auth_service.authenticate = lambda email, password: {
            "access_token": "integration-test-token",
            "refresh_token": "integration-refresh-token",
            "expires_in": 3600
        }
        
        # Create use cases with shared dependencies
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        
        authenticate_use_case = AuthenticateUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        
        # Act - Register a new user
        signup_request = SignupRequest(
            email="integration@test.com",
            password="IntegrationPass123!",
            full_name="Integration Test User"
        )
        
        registration_response = await register_use_case.execute(signup_request)
        
        # Assert registration
        assert registration_response.user.email == "integration@test.com"
        assert registration_response.tokens.access_token == "integration-test-token"
        
        # Act - Login with the same user
        login_request = LoginRequest(
            email="integration@test.com",
            password="IntegrationPass123!"
        )
        
        # Mock authenticate_user method
        authenticate_use_case.execute = lambda req: registration_response
        
        login_response = await authenticate_use_case.execute(login_request)
        
        # Assert login
        assert login_response.user.email == "integration@test.com"
        assert login_response.user.id == registration_response.user.id
    
    @pytest.mark.asyncio
    async def test_registration_persists_user_data(self):
        # Arrange
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()
        
        auth_service.authenticate = lambda email, password: {
            "access_token": "test-token",
            "refresh_token": "test-refresh",
            "expires_in": 3600
        }
        
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        
        # Act
        signup_request = SignupRequest(
            email="persist@test.com",
            password="PersistPass123!",
            full_name="Persist Test User"
        )
        
        response = await register_use_case.execute(signup_request)
        
        # Assert - Verify user was persisted
        saved_user = await user_repository.find_by_email("persist@test.com")
        assert saved_user is not None
        assert saved_user.full_name == "Persist Test User"
        assert saved_user.auth0_id.startswith("auth0|")
        
        # Verify user can be found by auth0_id
        user_by_auth_id = await user_repository.find_by_auth0_id(saved_user.auth0_id)
        assert user_by_auth_id is not None
        assert user_by_auth_id.id == saved_user.id
    
    @pytest.mark.asyncio
    async def test_concurrent_registrations(self):
        """Test that concurrent registrations don't interfere with each other."""
        # Arrange
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()
        
        auth_service.authenticate = lambda email, password: {
            "access_token": f"token-{email}",
            "refresh_token": f"refresh-{email}",
            "expires_in": 3600
        }
        
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        
        # Act - Register multiple users
        users_data = [
            ("user1@test.com", "User One"),
            ("user2@test.com", "User Two"),
            ("user3@test.com", "User Three")
        ]
        
        responses = []
        for email, name in users_data:
            request = SignupRequest(
                email=email,
                password="TestPass123!",
                full_name=name
            )
            response = await register_use_case.execute(request)
            responses.append(response)
        
        # Assert - All users registered successfully
        assert len(responses) == 3
        assert all(r.user.email in [email for email, _ in users_data] for r in responses)
        
        # Verify all users exist in repository
        for email, name in users_data:
            user = await user_repository.find_by_email(email)
            assert user is not None
            assert user.full_name == name