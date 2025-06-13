import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.core.dependencies import get_current_user_auth0_id, get_db

class TestRoleSearchEndpoints:
    """Test role search API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all endpoint dependencies."""
        with patch('src.api.v1.onboarding.part_1.JobMatchingService') as mock_service_class:
            # Create mock service instance
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance
            
            # Override FastAPI dependencies
            app.dependency_overrides[get_current_user_auth0_id] = lambda: "auth0|test123"
            app.dependency_overrides[get_db] = lambda: Mock()
            
            yield {
                'service_class': mock_service_class,
                'service': mock_service_instance
            }
            
            # Clear overrides after test
            app.dependency_overrides.clear()
    
    def test_search_roles_success(self, client, auth_headers, mock_dependencies):
        """Test successful role search."""
        # Setup mock service response
        mock_dependencies['service'].search_roles = AsyncMock(
            return_value={
                "matches": [
                    {
                        "id": "role1",
                        "title": "Software Engineer",
                        "description": "Develops software",
                        "industry_name": "Banking",
                        "confidence_score": 0.95
                    }
                ],
                "search_metadata": {
                    "user_id": "user123",
                    "industry_id": "ind123"
                }
            }
        )
        
        response = client.post(
            "/api/v1/onboarding/part-1/search-roles",
            headers=auth_headers,
            json={
                "job_title": "Software Developer",
                "job_description": "I write code and build applications"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["matches"]) == 1
        assert data["matches"][0]["title"] == "Software Engineer"
    
    def test_search_roles_validation_error(self, client, auth_headers, mock_dependencies):
        """Test role search with invalid input."""
        response = client.post(
            "/api/v1/onboarding/part-1/search-roles",
            headers=auth_headers,
            json={
                "job_title": "A",  # Too short
                "job_description": "Short"  # Too short
            }
        )
        
        assert response.status_code == 422
    
    def test_search_roles_unauthorized(self, client):
        """Test role search without authentication."""
        response = client.post(
            "/api/v1/onboarding/part-1/search-roles",
            json={
                "job_title": "Developer",
                "job_description": "I develop applications"
            }
        )
        
        assert response.status_code == 403
    
    def test_select_role_success(self, client, auth_headers, mock_dependencies):
        """Test successful role selection."""
        # Setup mock service response
        mock_dependencies['service'].select_role = AsyncMock(
            return_value={
                "success": True,
                "message": "Role selected successfully",
                "role_id": "role123",
                "is_custom": False
            }
        )
        
        response = client.post(
            "/api/v1/onboarding/part-1/select-role",
            headers=auth_headers,
            json={"role_id": "role123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["role_id"] == "role123"
        assert data["is_custom"] == False
    
    def test_select_custom_role_success(self, client, auth_headers, mock_dependencies):
        """Test successful custom role creation."""
        # Setup mock service response
        mock_dependencies['service'].select_role = AsyncMock(
            return_value={
                "success": True,
                "message": "Custom role created successfully",
                "role_id": "new-role-id",
                "is_custom": True
            }
        )
        
        response = client.post(
            "/api/v1/onboarding/part-1/select-role",
            headers=auth_headers,
            json={
                "custom_title": "Custom Developer",
                "custom_description": "I do custom development work"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["role_id"] == "new-role-id"
        assert data["is_custom"] == True