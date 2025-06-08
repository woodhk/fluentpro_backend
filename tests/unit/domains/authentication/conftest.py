import pytest
from unittest.mock import Mock
from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
from domains.authentication.services.interfaces import IAuthenticationService
from tests.mocks.repositories import MockUserRepository, MockRoleRepository
from tests.mocks.services import MockAuthenticationService

@pytest.fixture
def mock_user_repository():
    """Provide mock user repository for authentication domain tests"""
    return MockUserRepository()

@pytest.fixture
def mock_role_repository():
    """Provide mock role repository for authentication domain tests"""
    return MockRoleRepository()

@pytest.fixture
def mock_auth_service():
    """Provide mock authentication service"""
    return MockAuthenticationService()

@pytest.fixture
def authentication_container(mock_user_repository, mock_role_repository, mock_auth_service):
    """Provide complete authentication domain container"""
    from application.container import ApplicationContainer
    
    container = ApplicationContainer()
    container.repositories.user_repository.override(mock_user_repository)
    container.repositories.role_repository.override(mock_role_repository)
    container.services.auth_service.override(mock_auth_service)
    
    return container