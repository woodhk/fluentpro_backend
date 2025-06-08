"""
Global test configuration and fixtures.
Provides shared fixtures and test utilities for all test modules.
"""

import os
import sys
import asyncio
import pytest
import django
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, Generator, AsyncGenerator
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure Django settings - will be set up by pytest-django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings

# Import test utilities
from tests.fixtures.users import UserFactory, UserProfileFactory, RoleFactory
from tests.fixtures.test_data import TestDataGenerator, BulkDataGenerator
# from tests.fixtures.events import EventFixtures, UserEventFixtures, SessionEventFixtures
# from tests.fixtures.conversations import ConversationFixtures, MessageFixtures
from tests.mocks.services import (
    MockAuthenticationService, MockTokenService, MockEmbeddingService, 
    MockCompletionService, MockEventBus, MockCacheManager, 
    MockSessionStore, MockConversationStateManager
)
from tests.mocks.repositories import (
    MockUserRepository, MockRoleRepository, MockIndustryRepository, 
    MockPartnerRepository
    # MockEventStore  # Commented out due to import issues
)
from tests.mocks.external_services import (
    MockOpenAIClient, MockAuth0Client, MockAzureClient, MockRedisClient
)


# Event loop configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture(scope="function")
def db_session():
    """Provide a database session for tests."""
    # Django will handle database transactions automatically
    # This fixture exists for consistency with other frameworks
    yield


@pytest.fixture
def transactional_db():
    """Enable database access for tests that need it."""
    pass


# User and authentication fixtures
@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return UserFactory.create_user()


@pytest.fixture
def completed_user():
    """Create a user with completed onboarding."""
    return UserFactory.create_completed_user()


@pytest.fixture
def executive_user():
    """Create an executive user for testing."""
    return UserFactory.create_executive_user()


@pytest.fixture
def user_with_profile(sample_user):
    """Create a user with a complete profile."""
    profile = UserProfileFactory.create_complete_profile(sample_user)
    return {
        'user': sample_user,
        'profile': profile
    }


@pytest.fixture
def sample_role():
    """Create a sample role for testing."""
    return RoleFactory.create_role()


@pytest.fixture
def executive_role():
    """Create an executive role for testing."""
    return RoleFactory.create_executive_role()


# Mock service fixtures
@pytest.fixture
def mock_auth_service():
    """Provide mock authentication service."""
    return MockAuthenticationService()


@pytest.fixture
def mock_token_service():
    """Provide mock token service."""
    return MockTokenService()


@pytest.fixture
def mock_embedding_service():
    """Provide mock embedding service."""
    return MockEmbeddingService()


@pytest.fixture
def mock_completion_service():
    """Provide mock completion service."""
    return MockCompletionService()


@pytest.fixture
def mock_event_bus():
    """Provide mock event bus."""
    return MockEventBus()


@pytest.fixture
def mock_cache_manager():
    """Provide mock cache manager."""
    return MockCacheManager()


@pytest.fixture
def mock_session_store():
    """Provide mock session store."""
    return MockSessionStore()


@pytest.fixture
def mock_conversation_manager():
    """Provide mock conversation state manager."""
    return MockConversationStateManager()


# Mock repository fixtures
@pytest.fixture
def mock_user_repository():
    """Provide mock user repository."""
    return MockUserRepository()


@pytest.fixture
def mock_role_repository():
    """Provide mock role repository."""
    return MockRoleRepository()


@pytest.fixture
def mock_industry_repository():
    """Provide mock industry repository."""
    return MockIndustryRepository()


@pytest.fixture
def mock_partner_repository():
    """Provide mock partner repository."""
    return MockPartnerRepository()


# @pytest.fixture
# def mock_event_store():
#     """Provide mock event store."""
#     return MockEventStore()


# External service mocks
@pytest.fixture
def mock_openai_client():
    """Provide mock OpenAI client."""
    return MockOpenAIClient()


@pytest.fixture
def mock_auth0_client():
    """Provide mock Auth0 client."""
    return MockAuth0Client()


@pytest.fixture
def mock_azure_client():
    """Provide mock Azure client."""
    return MockAzureClient()


@pytest.fixture
def mock_redis_client():
    """Provide mock Redis client."""
    return MockRedisClient()


# Container and dependency injection fixtures
@pytest.fixture
def mock_container():
    """Provide a mock application container with all dependencies."""
    from application.container import ApplicationContainer
    
    container = ApplicationContainer()
    
    # Override with mocks
    container.repositories.user_repository.override(MockUserRepository())
    container.repositories.role_repository.override(MockRoleRepository())
    container.repositories.industry_repository.override(MockIndustryRepository())
    container.repositories.partner_repository.override(MockPartnerRepository())
    
    container.services.auth_service.override(MockAuthenticationService())
    container.services.token_service.override(MockTokenService())
    container.services.embedding_service.override(MockEmbeddingService())
    container.services.completion_service.override(MockCompletionService())
    
    container.infrastructure.event_bus.override(MockEventBus())
    container.infrastructure.cache_manager.override(MockCacheManager())
    container.infrastructure.session_store.override(MockSessionStore())
    
    container.external_services.openai_client.override(MockOpenAIClient())
    container.external_services.auth0_client.override(MockAuth0Client())
    container.external_services.azure_client.override(MockAzureClient())
    
    yield container
    
    # Reset container after test
    container.reset_last_provided()


# Test data fixtures
@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture
def bulk_data_generator():
    """Provide bulk data generator."""
    return BulkDataGenerator()


@pytest.fixture
def sample_user_data():
    """Generate sample user data."""
    return TestDataGenerator.generate_user_data()


@pytest.fixture
def sample_role_data():
    """Generate sample role data."""
    return TestDataGenerator.generate_role_data()


@pytest.fixture
def sample_industry_data():
    """Generate sample industry data."""
    return TestDataGenerator.generate_industry_data()


# Event fixtures
# @pytest.fixture
# def sample_user_event():
#     """Create a sample user event."""
#     return UserEventFixtures.create_user_created_event()


# @pytest.fixture
# def sample_session_event():
#     """Create a sample session event."""
#     return SessionEventFixtures.create_session_started_event()


# @pytest.fixture
# def event_scenario():
#     """Create a complete event scenario."""
#     from tests.fixtures.events import EventScenarioFixtures
#     return EventScenarioFixtures.create_user_registration_flow()


# Conversation fixtures
# @pytest.fixture
# def sample_conversation():
#     """Create a sample conversation state."""
#     return ConversationFixtures.create_active_conversation()


# @pytest.fixture
# def conversation_scenario():
#     """Create a complete conversation scenario."""
#     from tests.fixtures.conversations import ConversationScenarioFixtures
#     return ConversationScenarioFixtures.create_business_meeting_scenario()


# Environment and configuration fixtures
@pytest.fixture(scope="session")
def django_db_setup():
    """Set up test database."""
    pass


@pytest.fixture
def settings_override():
    """Override Django settings for testing."""
    from django.test import override_settings
    
    test_settings = {
        'DEBUG': True,
        'TESTING': True,
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        'CACHES': {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        'CELERY_TASK_ALWAYS_EAGER': True,
        'CELERY_TASK_EAGER_PROPAGATES': True,
    }
    
    return override_settings(**test_settings)


# Utility fixtures
@pytest.fixture
def freeze_time():
    """Provide time freezing utility for consistent test timing."""
    import freezegun
    frozen_time = datetime.utcnow()
    with freezegun.freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture
def isolated_test():
    """Ensure test runs in isolation with all dependencies mocked."""
    # This fixture can be used to mark tests that should run completely isolated
    pass


# Async utilities
@pytest.fixture
async def async_client():
    """Provide async test client for API testing."""
    from django.test import AsyncClient
    return AsyncClient()


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


# Performance testing fixtures
@pytest.fixture
def performance_threshold():
    """Set performance thresholds for tests."""
    return {
        'max_response_time': 1.0,  # seconds
        'max_memory_usage': 100,   # MB
        'max_db_queries': 10,      # number of queries
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically clean up after each test."""
    yield
    
    # Clear any global state
    # Reset mocks
    # Clean up temporary files
    # This runs after each test automatically


# Test markers utility
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


# Collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark slow tests
        if "slow" in item.nodeid or "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark external service tests
        if any(keyword in item.nodeid for keyword in ["openai", "auth0", "azure", "external"]):
            item.add_marker(pytest.mark.external)