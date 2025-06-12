from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, 
    SearchField, SearchFieldDataType, VectorSearch,
    HnswAlgorithmConfiguration, HnswParameters,
    VectorSearchProfile
)
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any, Optional
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class AzureSearchClient:
    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.api_key = settings.AZURE_SEARCH_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        self.credential = AzureKeyCredential(self.api_key)
        
        # Initialize clients
        self.index_client = SearchIndexClient(self.endpoint, self.credential)
        self.search_client = SearchClient(
            endpoint=self.endpoint, 
            index_name=self.index_name, 
            credential=self.credential
        )
    
    async def create_index(self):
        """Create Azure Search index for roles."""
        # Define the search index
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String, 
                          searchable=True, filterable=True),
            SearchableField(name="description", type=SearchFieldDataType.String, 
                          searchable=True),
            SimpleField(name="industry_id", type=SearchFieldDataType.String, 
                       filterable=True),
            SimpleField(name="industry_name", type=SearchFieldDataType.String, 
                       filterable=True),
            SimpleField(name="is_system_role", type=SearchFieldDataType.Boolean, 
                       filterable=True),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,  # OpenAI text-embedding-3-small
                vector_search_profile_name="role-vector-profile"
            )
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-algo",
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine"
                    )
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="role-vector-profile",
                    algorithm_configuration_name="hnsw-algo"
                )
            ]
        )
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        try:
            self.index_client.create_or_update_index(index)
            logger.info(f"Created/Updated Azure Search index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to create index: {str(e)}")
            raise
    
    async def upload_documents(self, documents: List[Dict[str, Any]]):
        """Upload documents to Azure Search index."""
        try:
            result = self.search_client.upload_documents(documents=documents)
            logger.info(f"Uploaded {len(documents)} documents to Azure Search")
            return result
        except Exception as e:
            logger.error(f"Failed to upload documents: {str(e)}")
            raise
    
    async def search_roles(
        self, 
        embedding: List[float], 
        industry_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar roles using vector search."""
        try:
            # Create vector query
            vector_query = VectorizedQuery(
                vector=embedding,
                k_nearest_neighbors=top_k,
                fields="embedding"
            )
            
            # Execute search with filter
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=f"industry_id eq '{industry_id}'",
                select=["id", "title", "description", "industry_name"],
                top=top_k
            )
            
            matches = []
            for result in results:
                matches.append({
                    "id": result["id"],
                    "title": result["title"],
                    "description": result["description"],
                    "industry_name": result["industry_name"],
                    "confidence_score": result["@search.score"]
                })
            
            return matches
        except Exception as e:
            logger.error(f"Failed to search roles: {str(e)}")
            raise
    
    async def delete_all_documents(self):
        """Delete all documents from the index."""
        try:
            # Search for all documents
            results = self.search_client.search(search_text="*", select=["id"])
            documents_to_delete = [{"id": result["id"]} for result in results]
            
            if documents_to_delete:
                self.search_client.delete_documents(documents=documents_to_delete)
                logger.info(f"Deleted {len(documents_to_delete)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise

# Global instance
azure_search_client = AzureSearchClient()