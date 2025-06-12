import pytest
from src.core.config import Settings

class TestRoleSearchConfiguration:
    """Test configuration for role search feature."""
    
    def test_openai_configuration_exists(self):
        """Test that OpenAI configuration is properly loaded."""
        settings = Settings()
        
        # These should fail initially (RED)
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'OPENAI_EMBEDDING_MODEL')
        assert settings.OPENAI_API_KEY is not None
        assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"
    
    def test_azure_search_configuration_exists(self):
        """Test that Azure Search configuration is properly loaded."""
        settings = Settings()
        
        # These should fail initially (RED)
        assert hasattr(settings, 'AZURE_SEARCH_ENDPOINT')
        assert hasattr(settings, 'AZURE_SEARCH_KEY')
        assert hasattr(settings, 'AZURE_SEARCH_INDEX_NAME')
        assert settings.AZURE_SEARCH_ENDPOINT is not None
        assert settings.AZURE_SEARCH_KEY is not None
        assert settings.AZURE_SEARCH_INDEX_NAME == "roles-index"