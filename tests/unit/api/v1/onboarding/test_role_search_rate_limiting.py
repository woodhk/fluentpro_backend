import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch, Mock
from src.core.dependencies import get_current_user_auth0_id, get_db

class TestRoleSearchRateLimiting:
    """Test rate limiting on role search endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication for all requests."""
        app.dependency_overrides[get_current_user_auth0_id] = lambda: "auth0|test123"
        app.dependency_overrides[get_db] = lambda: Mock()
        yield
        app.dependency_overrides.clear()
    
    def test_rate_limiting_on_search_endpoint(self, client, mock_auth):
        """Test that rate limiting works on search endpoint."""
        # Mock the service to avoid actual processing
        with patch('src.api.v1.onboarding.part_1.JobMatchingService') as mock_service:
            mock_instance = Mock()
            mock_service.return_value = mock_instance
            mock_instance.search_roles.return_value = {
                "matches": [],
                "search_metadata": {}
            }
            
            # Make multiple requests
            auth_headers = {"Authorization": "Bearer test-token"}
            responses = []
            
            # API_RATE_LIMIT is 100/minute, so make 101 requests
            for i in range(101):
                response = client.post(
                    "/api/v1/onboarding/part-1/search-roles",
                    headers=auth_headers,
                    json={
                        "job_title": f"Developer {i}",
                        "job_description": "I develop applications and software"
                    }
                )
                responses.append(response)
                
                # Stop early if we hit rate limit
                if response.status_code == 429:
                    break
            
            # Check that we hit the rate limit
            rate_limited = any(r.status_code == 429 for r in responses)
            assert rate_limited == True, "Should hit rate limit after 100 requests"