import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.core.dependencies import get_current_user, get_db

class TestAdminEndpoints:
    """Test admin endpoints for role management."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def admin_headers(self):
        return {"Authorization": "Bearer admin-token"}
    
    @pytest.fixture
    def mock_admin_dependencies(self):
        with patch('src.api.v1.admin.AzureSearchService') as mock_service:
            # Mock user
            app.dependency_overrides[get_current_user] = lambda: {
                "id": "admin123",
                "email": "admin@fluentpro.com",
                "is_admin": True
            }
            
            # Mock database
            app.dependency_overrides[get_db] = lambda: Mock()
            
            # Mock service instance
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            
            yield {
                'service': mock_service_instance
            }
            
            app.dependency_overrides.clear()
    
    def test_reindex_roles_success(self, client, admin_headers, mock_admin_dependencies):
        """Test successful role reindexing."""
        # Setup mock response
        mock_admin_dependencies['service'].reindex_all_roles = AsyncMock(
            return_value={
                "success": True,
                "total_roles": 50,
                "documents_indexed": 50
            }
        )
        
        response = client.post(
            "/api/v1/admin/reindex-roles",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["total_roles"] == 50
        assert data["documents_indexed"] == 50
    
    def test_generate_embeddings_success(self, client, admin_headers, mock_admin_dependencies):
        """Test generating missing embeddings."""
        # Setup mock response
        mock_admin_dependencies['service'].generate_missing_embeddings = AsyncMock(
            return_value={
                "success": True,
                "embeddings_generated": 10
            }
        )
        
        response = client.post(
            "/api/v1/admin/generate-embeddings",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["embeddings_generated"] == 10
    
    def test_admin_endpoints_unauthorized(self, client):
        """Test admin endpoints without authentication."""
        response = client.post("/api/v1/admin/reindex-roles")
        assert response.status_code == 403
        
        response = client.post("/api/v1/admin/generate-embeddings")
        assert response.status_code == 403