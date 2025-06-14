import pytest
from unittest.mock import Mock, patch

# Import all components to verify they exist
from src.core.config import settings
from src.integrations.openai import OpenAIClient, openai_client
from src.integrations.azure_search import AzureSearchClient, azure_search_client
from src.repositories.onboarding.job_roles_repository import JobRolesRepository
from src.services.onboarding.job_matching_service import JobMatchingService
from src.services.onboarding.azure_search_service import AzureSearchService
from src.schemas.onboarding.part_1 import (
    RoleSearchRequest, RoleSearchResponse,
    RoleSelectionRequest, RoleSelectionResponse
)
from src.api.v1.admin import router as admin_router

class TestRoleSearchComplete:
    """Comprehensive tests for role search feature."""
    
    def test_all_components_exist(self):
        """Verify all required components exist."""
        # Configuration
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'AZURE_SEARCH_ENDPOINT')
        assert hasattr(settings, 'AZURE_SEARCH_KEY')
        
        # Integrations
        assert OpenAIClient is not None
        assert openai_client is not None
        assert AzureSearchClient is not None
        assert azure_search_client is not None
        
        # Repositories
        assert JobRolesRepository is not None
        
        # Services
        assert JobMatchingService is not None
        assert AzureSearchService is not None
        
        # Schemas
        assert RoleSearchRequest is not None
        assert RoleSearchResponse is not None
        assert RoleSelectionRequest is not None
        assert RoleSelectionResponse is not None
        
        # Admin router
        assert admin_router is not None
    
    @pytest.mark.asyncio
    async def test_openai_client_initialization(self):
        """Test OpenAI client can be initialized."""
        with patch('src.integrations.openai.OpenAI') as mock_openai:
            mock_openai.return_value = Mock()
            client = OpenAIClient()
            assert client.client is not None
            assert client.embedding_model == "text-embedding-3-small"
    
    @pytest.mark.asyncio
    async def test_azure_search_client_initialization(self):
        """Test Azure Search client can be initialized."""
        with patch('src.integrations.azure_search.SearchIndexClient') as mock_index, \
             patch('src.integrations.azure_search.SearchClient') as mock_search:
            
            mock_index.return_value = Mock()
            mock_search.return_value = Mock()
            
            client = AzureSearchClient()
            assert client.endpoint is not None
            assert client.index_name == "roles-index"
    
    def test_schema_validation(self):
        """Test schema validation works correctly."""
        # Valid request
        valid_request = RoleSearchRequest(
            job_title="Software Engineer",
            job_description="I develop software applications"
        )
        assert valid_request.job_title == "Software Engineer"
        
        # Invalid request - short title
        with pytest.raises(Exception):
            RoleSearchRequest(
                job_title="A",
                job_description="Valid description here"
            )
        
        # Invalid request - short description
        with pytest.raises(Exception):
            RoleSearchRequest(
                job_title="Valid Title",
                job_description="Short"
            )
    
    @pytest.mark.asyncio
    async def test_complete_flow_mock(self):
        """Test complete flow with all mocks."""
        # Mock database
        mock_db = Mock()
        mock_db.table = Mock(return_value=mock_db)
        mock_db.select = Mock(return_value=mock_db)
        mock_db.eq = Mock(return_value=mock_db)
        mock_db.execute = Mock(return_value=Mock(data=[{
            "id": "user123",
            "auth0_id": "auth0|test",
            "industry_id": "ind123"
        }]))
        
        # Mock OpenAI client generate_embedding method
        with patch('src.integrations.openai.openai_client.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            # Mock Azure Search client search_roles method
            with patch('src.integrations.azure_search.azure_search_client.search_roles') as mock_search:
                mock_search.return_value = [{
                    "id": "role1",
                    "title": "Software Engineer",  
                    "description": "Develops software",
                    "industry_name": "Technology",
                    "confidence_score": 0.95
                }]
                
                # Test the service
                service = JobMatchingService(mock_db)
                result = await service.search_roles(
                    auth0_id="auth0|test",
                    job_title="Software Engineer",
                    job_description="I build applications"
                )
                
                assert "matches" in result
                assert len(result["matches"]) == 1
                assert result["matches"][0]["title"] == "Software Engineer"
                assert result["matches"][0]["confidence_score"] == 0.95