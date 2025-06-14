import pytest
from unittest.mock import Mock, patch
from src.integrations.openai import OpenAIClient

class TestOpenAIClient:
    """Test OpenAI client integration."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        with patch('src.integrations.openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client
    
    def test_openai_client_initialization(self, mock_openai_client):
        """Test OpenAI client initializes correctly."""
        # This should fail initially (RED)
        client = OpenAIClient()
        
        assert client.client is not None
        assert client.embedding_model == "text-embedding-3-small"
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_openai_client):
        """Test successful embedding generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # This should fail initially (RED)
        client = OpenAIClient()
        client.client = mock_openai_client
        
        result = await client.generate_embedding("test text")
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert result == [0.1, 0.2, 0.3]
        
        # Verify the API was called correctly
        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="test text"
        )
    
    @pytest.mark.asyncio
    async def test_generate_embedding_error_handling(self, mock_openai_client):
        """Test error handling in embedding generation."""
        # Setup mock to raise exception
        mock_openai_client.embeddings.create.side_effect = Exception("API Error")
        
        # This should fail initially (RED)
        client = OpenAIClient()
        client.client = mock_openai_client
        
        with pytest.raises(Exception) as exc_info:
            await client.generate_embedding("test text")
        
        assert "Embedding generation failed: API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_openai_client):
        """Test batch embedding generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        # This should fail initially (RED)
        client = OpenAIClient()
        client.client = mock_openai_client
        
        texts = ["text1", "text2"]
        result = await client.generate_embeddings_batch(texts)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]