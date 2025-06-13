import pytest
from fastapi.testclient import TestClient
from src.main import app
import os
from unittest.mock import patch, Mock, AsyncMock

@pytest.mark.integration
class TestRoleSearchE2E:
    """End-to-end tests for role search feature."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Valid authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_all_services(self):
        """Mock all external services for E2E testing."""
        with patch('src.core.dependencies.get_current_user_auth0_id') as mock_auth, \
             patch('src.integrations.openai.OpenAI') as mock_openai_class, \
             patch('src.integrations.azure_search.SearchClient') as mock_search_client, \
             patch('src.integrations.azure_search.SearchIndexClient') as mock_index_client, \
             patch('src.core.database.get_supabase_client') as mock_db_client:
            
            # Mock auth
            mock_auth.return_value = "auth0|test123"
            
            # Mock database
            mock_db = Mock()
            mock_db.table = Mock(return_value=mock_db)
            mock_db.select = Mock(return_value=mock_db)
            mock_db.insert = Mock(return_value=mock_db)
            mock_db.update = Mock(return_value=mock_db)
            mock_db.eq = Mock(return_value=mock_db)
            mock_db_client.return_value = mock_db
            
            # Mock OpenAI
            mock_openai = Mock()
            mock_openai_class.return_value = mock_openai
            mock_embedding_response = Mock()
            mock_embedding_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_openai.embeddings.create.return_value = mock_embedding_response
            
            # Mock Azure Search
            mock_search = Mock()
            mock_search_client.return_value = mock_search
            
            yield {
                'auth': mock_auth,
                'db': mock_db,
                'openai': mock_openai,
                'azure_search': mock_search
            }
    
    def test_complete_role_search_flow(self, client, auth_headers, mock_all_services):
        """Test the complete flow from search to selection."""
        # Setup database responses
        mock_all_services['db'].execute.side_effect = [
            # get_user_by_auth0_id for search
            Mock(data=[{
                "id": "user123",
                "auth0_id": "auth0|test123",
                "industry_id": "ind-banking"
            }]),
            # get_user_by_auth0_id for selection
            Mock(data=[{
                "id": "user123",
                "auth0_id": "auth0|test123",
                "industry_id": "ind-banking"
            }])
        ]
        
        # Setup Azure Search results
        mock_all_services['azure_search'].search.return_value = [
            {
                "id": "role1",
                "title": "Software Engineer",
                "description": "Develops software",
                "industry_name": "Banking & Finance",
                "@search.score": 0.95
            }
        ]
        
        # Step 1: Search for roles
        search_response = client.post(
            "/api/v1/onboarding/part-1/search-roles",
            headers=auth_headers,
            json={
                "job_title": "Software Engineer",
                "job_description": "I develop web applications using Python and JavaScript"
            }
        )
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["success"] == True
        assert len(search_data["matches"]) > 0
        
        # Step 2: Select a role
        selected_role_id = search_data["matches"][0]["id"]
        
        # Setup update response
        update_mock = Mock()
        update_mock.execute.return_value = Mock(data=[{
            "id": "user123",
            "selected_role_id": selected_role_id
        }])
        mock_all_services['db'].table.return_value.update.return_value.eq.return_value = update_mock
        
        select_response = client.post(
            "/api/v1/onboarding/part-1/select-role",
            headers=auth_headers,
            json={"role_id": selected_role_id}
        )
        
        assert select_response.status_code == 200
        select_data = select_response.json()
        assert select_data["success"] == True
        assert select_data["role_id"] == selected_role_id
        assert select_data["is_custom"] == False
    
    def test_custom_role_flow(self, client, auth_headers, mock_all_services):
        """Test custom role creation flow."""
        # Setup database responses
        mock_all_services['db'].execute.side_effect = [
            # get_user_by_auth0_id
            Mock(data=[{
                "id": "user123",
                "auth0_id": "auth0|test123",
                "industry_id": "ind-tech"
            }]),
            # create_custom_role
            Mock(data=[{
                "id": "custom-role-123",
                "title": "Blockchain Developer",
                "description": "Develops smart contracts",
                "embedding_vector": [0.1] * 1536
            }]),
            # get industry name for indexing
            Mock(data=[{"name": "Technology"}])
        ]
        
        # Setup update response
        update_mock = Mock()
        update_mock.execute.return_value = Mock(data=[{
            "id": "user123",
            "selected_role_id": "custom-role-123"
        }])
        mock_all_services['db'].table.return_value.update.return_value.eq.return_value = update_mock
        
        # Mock Azure upload
        mock_all_services['azure_search'].upload_documents.return_value = Mock()
        
        # Create custom role
        response = client.post(
            "/api/v1/onboarding/part-1/select-role",
            headers=auth_headers,
            json={
                "custom_title": "Blockchain Developer",
                "custom_description": "I develop smart contracts and decentralized applications"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["is_custom"] == True
        assert data["role_id"] == "custom-role-123"