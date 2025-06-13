import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from src.integrations.openai import OpenAIClient
from src.integrations.azure_search import AzureSearchClient

@pytest.mark.performance
class TestRoleSearchPerformance:
    """Performance tests for role search."""
    
    @pytest.mark.asyncio
    async def test_embedding_generation_performance(self):
        """Test OpenAI embedding generation performance."""
        with patch('src.integrations.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock fast response
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            
            client = OpenAIClient()
            
            texts = [
                "Software Engineer developing web applications",
                "Data Scientist working with machine learning",
                "Product Manager leading agile teams",
                "DevOps Engineer managing cloud infrastructure",
                "UX Designer creating user interfaces"
            ]
            
            start_time = time.time()
            
            # Generate embeddings
            tasks = [client.generate_embedding(text) for text in texts]
            embeddings = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(embeddings) == 5
            assert all(len(emb) == 1536 for emb in embeddings)
            assert duration < 5.0  # Should complete within 5 seconds
            
            print(f"Generated {len(embeddings)} embeddings in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self):
        """Test batch embedding generation performance."""
        with patch('src.integrations.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock batch response
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1] * 1536) for _ in range(20)
            ]
            mock_client.embeddings.create.return_value = mock_response
            
            client = OpenAIClient()
            
            # Test with 20 texts
            texts = [f"Job description {i}: Developer working on various projects" for i in range(20)]
            
            start_time = time.time()
            embeddings = await client.generate_embeddings_batch(texts)
            end_time = time.time()
            
            duration = end_time - start_time
            
            assert len(embeddings) == 20
            assert duration < 10.0  # Should complete within 10 seconds
            
            print(f"Batch generated {len(embeddings)} embeddings in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_search_performance(self):
        """Test Azure Search query performance."""
        with patch('src.integrations.azure_search.SearchClient') as mock_search_class:
            mock_search = Mock()
            mock_search_class.return_value = mock_search
            
            # Mock search results
            mock_results = [
                {
                    "id": f"role{i}",
                    "title": f"Role {i}",
                    "description": f"Description {i}",
                    "industry_name": "Technology",
                    "@search.score": 0.9 - (i * 0.1)
                }
                for i in range(5)
            ]
            mock_search.search.return_value = mock_results
            
            client = AzureSearchClient()
            
            start_time = time.time()
            
            # Perform multiple searches
            searches = []
            for i in range(10):
                embedding = [0.1] * 1536
                result = await client.search_roles(
                    embedding=embedding,
                    industry_id="ind123",
                    top_k=5
                )
                searches.append(result)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(searches) == 10
            assert all(len(s) == 5 for s in searches)
            assert duration < 5.0  # 10 searches should complete within 5 seconds
            
            print(f"Performed {len(searches)} searches in {duration:.2f} seconds")