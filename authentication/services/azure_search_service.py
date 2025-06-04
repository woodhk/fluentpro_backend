from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    VectorSearchAlgorithmKind
)
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any, Optional
from decouple import config
import json
from .openai_service import OpenAIService


class AzureSearchService:
    """
    Service class for interacting with Azure AI Search
    """
    
    def __init__(self):
        self.endpoint = config('AZURE_SEARCH_ENDPOINT')
        self.api_key = config('AZURE_SEARCH_KEY')
        self.api_version = config('AZURE_SEARCH_API_VERSION', default='2024-07-01')
        self.credential = AzureKeyCredential(self.api_key)
        
        # Index name for roles
        self.roles_index_name = "roles-index"
        
        # Initialize clients
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.roles_index_name,
            credential=self.credential
        )
        
        # Initialize OpenAI service for on-the-fly embedding generation
        self.openai_service = OpenAIService()
    
    def create_roles_index(self) -> Dict[str, Any]:
        """
        Create the search index for roles with vector search capabilities
        """
        try:
            # Define the search fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, 
                              analyzer_name="en.microsoft"),
                SearchableField(name="description", type=SearchFieldDataType.String, 
                              analyzer_name="en.microsoft"),
                SimpleField(name="industry_id", type=SearchFieldDataType.String),
                SearchableField(name="industry_name", type=SearchFieldDataType.String, 
                              analyzer_name="en.microsoft", filterable=True),
                SimpleField(name="hierarchy_level", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True),
                SearchableField(name="search_keywords", type=SearchFieldDataType.String,
                              analyzer_name="en.microsoft"),
                SearchField(name="embedding_vector", 
                          type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                          searchable=True, 
                          vector_search_dimensions=1536,
                          vector_search_profile_name="role-embedding-profile"),
                SimpleField(name="is_active", type=SearchFieldDataType.Boolean, filterable=True),
                SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, 
                          filterable=True, sortable=True)
            ]
            
            # Configure vector search with optimized parameters for better relevancy
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="role-hnsw-algorithm",
                        kind=VectorSearchAlgorithmKind.HNSW,
                        parameters={
                            "m": 10,  # Maximum allowed value for better recall
                            "efConstruction": 800,  # Higher for better index quality
                            "efSearch": 1000,  # Higher for better search quality
                            "metric": "cosine"
                        }
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="role-embedding-profile",
                        algorithm_configuration_name="role-hnsw-algorithm"
                    )
                ]
            )
            
            # Configure semantic search
            semantic_config = SemanticConfiguration(
                name="role-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[
                        SemanticField(field_name="description"),
                        SemanticField(field_name="industry_name")
                    ],
                    keywords_fields=[
                        SemanticField(field_name="search_keywords")
                    ]
                )
            )
            
            semantic_search = SemanticSearch(configurations=[semantic_config])
            
            # Create the search index
            index = SearchIndex(
                name=self.roles_index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search
            )
            
            # Create or update the index
            result = self.index_client.create_or_update_index(index)
            
            return {
                'success': True,
                'index_name': result.name,
                'message': f'Index "{result.name}" created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create index: {str(e)}'
            }
    
    def upload_roles_to_index(self, roles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload role data to the search index with on-the-fly embedding generation
        """
        try:
            # Prepare documents for upload
            documents = []
            
            for role in roles_data:
                print(f"   🔄 Processing: {role.get('title', 'Unknown')}")
                
                # Generate embedding on-the-fly using OpenAI
                try:
                    embedding_vector = self.openai_service.embed_role(role)
                    print(f"      ✅ Generated embedding: {len(embedding_vector)} dimensions")
                except Exception as e:
                    print(f"      ❌ Failed to generate embedding: {str(e)}")
                    continue
                
                # Convert search_keywords to a searchable string
                search_keywords = role.get('search_keywords', [])
                if search_keywords is None:
                    search_keywords_str = ""
                elif isinstance(search_keywords, list):
                    # Join array elements into a single searchable string
                    search_keywords_str = " ".join(search_keywords)
                elif isinstance(search_keywords, str):
                    search_keywords_str = search_keywords
                else:
                    search_keywords_str = str(search_keywords)
                
                # Ensure created_at is in proper format
                created_at = role.get('created_at')
                if created_at and isinstance(created_at, str):
                    # Convert to ISO format if needed
                    try:
                        from datetime import datetime
                        if 'T' not in created_at:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).isoformat()
                    except:
                        created_at = None
                
                document = {
                    "id": role['id'],
                    "title": role['title'],
                    "description": role['description'],
                    "industry_id": role['industry_id'],
                    "industry_name": role['industry_name'],
                    "hierarchy_level": role['hierarchy_level'],
                    "search_keywords": search_keywords_str,
                    "embedding_vector": embedding_vector,
                    "is_active": role.get('is_active', True),
                    "created_at": created_at
                }
                
                documents.append(document)
            
            if not documents:
                return {
                    'success': False,
                    'error': 'No valid documents to upload'
                }
            
            # Upload documents to the index
            result = self.search_client.upload_documents(documents)
            
            # Check results
            successful_uploads = 0
            failed_uploads = 0
            
            for upload_result in result:
                if upload_result.succeeded:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                    print(f"Failed to upload document {upload_result.key}: {upload_result.error_message}")
            
            return {
                'success': failed_uploads == 0,
                'successful_uploads': successful_uploads,
                'failed_uploads': failed_uploads,
                'total_documents': len(documents),
                'message': f'Uploaded {successful_uploads}/{len(documents)} documents successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to upload documents: {str(e)}'
            }
    
    def search_similar_roles(self, query_embedding: List[float], 
                           top_k: int = 5, 
                           filters: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for similar roles using vector similarity
        """
        try:
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields="embedding_vector"
            )
            
            # Perform search
            search_results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filters,
                select=["id", "title", "description", "industry_name", "hierarchy_level", "search_keywords"],
                top=top_k
            )
            
            # Process results
            results = []
            for result in search_results:
                results.append({
                    'id': result['id'],
                    'title': result['title'],
                    'description': result['description'],
                    'industry_name': result['industry_name'],
                    'hierarchy_level': result['hierarchy_level'],
                    'search_keywords': result.get('search_keywords', []),
                    'score': result['@search.score']
                })
            
            return {
                'success': True,
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Search failed: {str(e)}',
                'results': []
            }
    
    def hybrid_search_roles(self, text_query: str, 
                           query_embedding: List[float], 
                           top_k: int = 5,
                           filters: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform hybrid search combining text and vector search with improved scoring
        """
        try:
            # Create vector query with weight for better hybrid search balance
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k * 3,  # Get more candidates for better ranking
                fields="embedding_vector",
                weight=0.6  # Give vector search more weight for semantic matching
            )
            
            # Perform hybrid search with semantic ranking
            search_results = self.search_client.search(
                search_text=text_query,
                vector_queries=[vector_query],
                filter=filters,
                select=["id", "title", "description", "industry_name", "hierarchy_level", "search_keywords"],
                top=top_k,
                query_type="semantic",
                semantic_configuration_name="role-semantic-config",
                query_caption="extractive",
                query_answer="extractive"
            )
            
            # Process results with improved scoring
            results = []
            for result in search_results:
                # Get the actual search score and normalize it
                raw_score = result.get('@search.score', 0)
                
                # Improved scoring algorithm
                # Azure Search semantic scores typically range from 0.01 to 0.1+ for good matches
                # We need to transform this to a more useful 0-1 scale
                
                title_lower = result['title'].lower()
                query_lower = text_query.lower()
                
                # Base score transformation - use a more aggressive scaling
                # Map 0.025 -> 0.7, 0.03 -> 0.8, 0.04+ -> 0.9+
                import math
                if raw_score <= 0.01:
                    base_score = raw_score * 10  # Very low scores stay low
                elif raw_score <= 0.025:
                    base_score = 0.5 + (raw_score - 0.01) * 13.33  # Map 0.01-0.025 to 0.5-0.7
                elif raw_score <= 0.035:
                    base_score = 0.7 + (raw_score - 0.025) * 20  # Map 0.025-0.035 to 0.7-0.9
                else:
                    base_score = 0.9 + min((raw_score - 0.035) * 10, 0.1)  # 0.035+ maps to 0.9-1.0
                
                relevance_score = min(base_score, 1.0)
                
                # Boost for exact title matches
                query_words = set(query_lower.split())
                title_words = set(title_lower.split())
                
                # Check for exact title match
                if title_lower.strip() in query_lower or any(title_lower.startswith(word) for word in query_words if len(word) > 3):
                    relevance_score = min(relevance_score * 1.4, 1.0)
                
                # Boost for significant word overlap
                word_overlap = len(query_words.intersection(title_words))
                if word_overlap >= 2:
                    relevance_score = min(relevance_score * 1.2, 1.0)
                elif word_overlap >= 1:
                    relevance_score = min(relevance_score * 1.1, 1.0)
                
                results.append({
                    'id': result['id'],
                    'title': result['title'],
                    'description': result['description'],
                    'industry_name': result['industry_name'],
                    'hierarchy_level': result['hierarchy_level'],
                    'search_keywords': result.get('search_keywords', []),
                    'score': relevance_score,  # Use improved relevance score
                    'raw_score': raw_score,  # Keep original for debugging
                    'semantic_caption': result.get('@search.captions', [])
                })
            
            # Sort by improved relevance score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'success': True,
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Hybrid search failed: {str(e)}',
                'results': []
            }
    
    def delete_index(self) -> Dict[str, Any]:
        """
        Delete the roles index (useful for testing/cleanup)
        """
        try:
            self.index_client.delete_index(self.roles_index_name)
            return {
                'success': True,
                'message': f'Index "{self.roles_index_name}" deleted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete index: {str(e)}'
            }
    
    def add_single_role_to_index(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a single new role to the Azure AI Search index with on-the-fly embedding generation
        """
        try:
            print(f"   🔄 Adding new role to Azure Search: {role_data.get('title', 'Unknown')}")
            
            # Generate embedding on-the-fly using OpenAI
            try:
                embedding_vector = self.openai_service.embed_role(role_data)
                print(f"      ✅ Generated embedding: {len(embedding_vector)} dimensions")
            except Exception as e:
                print(f"      ❌ Failed to generate embedding: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to generate embedding: {str(e)}'
                }
            
            # Convert search_keywords to a searchable string
            search_keywords = role_data.get('search_keywords', [])
            if search_keywords is None:
                search_keywords_str = ""
            elif isinstance(search_keywords, list):
                # Join array elements into a single searchable string
                search_keywords_str = " ".join(search_keywords)
            elif isinstance(search_keywords, str):
                search_keywords_str = search_keywords
            else:
                search_keywords_str = str(search_keywords)
            
            # Ensure created_at is in proper format
            created_at = role_data.get('created_at')
            if created_at and isinstance(created_at, str):
                # Convert to ISO format if needed
                try:
                    from datetime import datetime
                    if 'T' not in created_at:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00')).isoformat()
                except:
                    created_at = None
            
            document = {
                "id": role_data['id'],
                "title": role_data['title'],
                "description": role_data['description'],
                "industry_id": role_data['industry_id'],
                "industry_name": role_data['industry_name'],
                "hierarchy_level": role_data['hierarchy_level'],
                "search_keywords": search_keywords_str,
                "embedding_vector": embedding_vector,
                "is_active": role_data.get('is_active', True),
                "created_at": created_at
            }
            
            # Upload document to the index
            result = self.search_client.upload_documents([document])
            
            # Check results
            upload_result = result[0]
            if upload_result.succeeded:
                print(f"      ✅ Successfully added role to Azure Search index")
                return {
                    'success': True,
                    'message': f'Role "{role_data["title"]}" added to search index successfully',
                    'role_id': role_data['id']
                }
            else:
                print(f"      ❌ Failed to upload role: {upload_result.error_message}")
                return {
                    'success': False,
                    'error': f'Failed to upload role: {upload_result.error_message}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to add role to index: {str(e)}'
            }