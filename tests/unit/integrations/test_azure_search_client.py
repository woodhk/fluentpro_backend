import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.integrations.azure_search import AzureSearchClient

class TestAzureSearchClient:
    """Test Azure Search client integration."""
    
    @pytest.fixture
    def mock_search_clients(self):
        """Mock Azure Search clients."""
        with patch('src.integrations.azure_search.SearchIndexClient') as mock_index_client, \
             patch('src.integrations.azure_search.SearchClient') as mock_search_client, \
             patch('src.integrations.azure_search.AzureKeyCredential') as mock_credential:
            
            yield {
                'index_client': mock_index_client,
                'search_client': mock_search_client,
                'credential': mock_credential
            }
    
    def test_azure_search_client_initialization(self, mock_search_clients):
        """Test Azure Search client initializes correctly."""
        # This should fail initially (RED)
        client = AzureSearchClient()
        
        assert client.endpoint is not None
        assert client.api_key is not None
        assert client.index_name == "roles-index"
        assert client.index_client is not None
        assert client.search_client is not None
    
    @pytest.mark.asyncio
    async def test_create_index(self, mock_search_clients):
        """Test index creation."""
        # This should fail initially (RED)
        client = AzureSearchClient()
        mock_index_client = Mock()
        client.index_client = mock_index_client
        
        await client.create_index()
        
        # Verify index was created
        mock_index_client.create_or_update_index.assert_called_once()
        
        # Verify the index configuration
        call_args = mock_index_client.create_or_update_index.call_args[0]
        index = call_args[0]
        
        assert index.name == "roles-index"
        assert len(index.fields) >= 7  # At least 7 fields
    
    @pytest.mark.asyncio
    async def test_upload_documents(self, mock_search_clients):
        """Test document upload."""
        # This should fail initially (RED)
        client = AzureSearchClient()
        mock_search_client = Mock()
        mock_search_client.upload_documents.return_value = Mock()
        client.search_client = mock_search_client
        
        documents = [
            {"id": "1", "title": "Software Engineer", "embedding": [0.1, 0.2]}
        ]
        
        await client.upload_documents(documents)
        
        mock_search_client.upload_documents.assert_called_once_with(
            documents=documents
        )
    
    @pytest.mark.asyncio
    async def test_search_roles(self, mock_search_clients):
        """Test role search functionality."""
        # Setup mock search results
        mock_results = [
            {
                "id": "role1",
                "title": "Software Engineer",
                "description": "Develops software",
                "industry_name": "Banking & Finance",
                "@search.score": 0.95
            }
        ]
        
        # This should fail initially (RED)
        client = AzureSearchClient()
        mock_search_client = Mock()
        mock_search_client.search.return_value = mock_results
        client.search_client = mock_search_client
        
        embedding = [0.1] * 1536
        industry_id = "industry123"
        
        results = await client.search_roles(
            embedding=embedding,
            industry_id=industry_id,
            top_k=5
        )
        
        assert len(results) == 1
        assert results[0]["id"] == "role1"
        assert results[0]["confidence_score"] == 0.95
        
        # Verify search was called correctly
        mock_search_client.search.assert_called_once()