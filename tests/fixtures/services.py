from tests.mocks.services import (
    MockAuthenticationService,
    MockTokenService,
    MockEmbeddingService,
    MockCompletionService
)

def create_test_services():
    """Create mock services for testing"""
    return {
        'auth_service': MockAuthenticationService(),
        'token_service': MockTokenService(),
        'embedding_service': MockEmbeddingService(),
        'completion_service': MockCompletionService()
    }