"""
Azure Services Client Interfaces

Defines contracts for Azure service implementations including
Azure OpenAI and Azure Cognitive Search.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple


class IAzureOpenAIClient(ABC):
    """
    Azure OpenAI client interface for LLM and embedding operations.
    
    Provides access to OpenAI models deployed on Azure infrastructure.
    """
    
    @abstractmethod
    def create_completion(self,
                         prompt: str,
                         deployment_name: str,
                         max_tokens: Optional[int] = None,
                         temperature: float = 0.7,
                         top_p: float = 1.0,
                         frequency_penalty: float = 0.0,
                         presence_penalty: float = 0.0,
                         stop: Optional[List[str]] = None) -> str:
        """
        Create a text completion using Azure OpenAI.
        
        Args:
            prompt: The prompt to complete
            deployment_name: Azure deployment name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            stop: Stop sequences
            
        Returns:
            Generated completion text
            
        Raises:
            AzureOpenAIError: If completion fails
        """
        pass
    
    @abstractmethod
    def create_chat_completion(self,
                             messages: List[Dict[str, str]],
                             deployment_name: str,
                             max_tokens: Optional[int] = None,
                             temperature: float = 0.7,
                             top_p: float = 1.0,
                             frequency_penalty: float = 0.0,
                             presence_penalty: float = 0.0) -> Dict[str, Any]:
        """
        Create a chat completion using Azure OpenAI.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            deployment_name: Azure deployment name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            
        Returns:
            Dict containing generated message and metadata
            
        Raises:
            AzureOpenAIError: If chat completion fails
        """
        pass
    
    @abstractmethod
    def create_embedding(self,
                        text: str,
                        deployment_name: str) -> List[float]:
        """
        Create an embedding vector using Azure OpenAI.
        
        Args:
            text: Text to embed
            deployment_name: Azure embedding deployment name
            
        Returns:
            Embedding vector
            
        Raises:
            AzureOpenAIError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def create_embeddings_batch(self,
                               texts: List[str],
                               deployment_name: str,
                               batch_size: int = 16) -> List[List[float]]:
        """
        Create embedding vectors for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            deployment_name: Azure embedding deployment name
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
            
        Raises:
            AzureOpenAIError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_deployment_info(self, deployment_name: str) -> Dict[str, Any]:
        """
        Get information about an Azure OpenAI deployment.
        
        Args:
            deployment_name: Deployment name
            
        Returns:
            Deployment information including model and version
            
        Raises:
            AzureOpenAIError: If retrieval fails
        """
        pass


class IAzureCognitiveSearchClient(ABC):
    """
    Azure Cognitive Search client interface for vector search operations.
    
    Provides semantic search capabilities using Azure infrastructure.
    """
    
    @abstractmethod
    def create_index(self,
                    index_name: str,
                    fields: List[Dict[str, Any]],
                    vector_search_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a search index.
        
        Args:
            index_name: Name of the index
            fields: List of field definitions
            vector_search_config: Optional vector search configuration
            
        Returns:
            True if index created successfully
            
        Raises:
            AzureSearchError: If creation fails
        """
        pass
    
    @abstractmethod
    def delete_index(self, index_name: str) -> bool:
        """
        Delete a search index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            AzureSearchError: If deletion fails
        """
        pass
    
    @abstractmethod
    def index_documents(self,
                       index_name: str,
                       documents: List[Dict[str, Any]],
                       batch_size: int = 100) -> Dict[str, Any]:
        """
        Index documents in batches.
        
        Args:
            index_name: Name of the index
            documents: List of documents to index
            batch_size: Number of documents per batch
            
        Returns:
            Dict containing indexing results
            
        Raises:
            AzureSearchError: If indexing fails
        """
        pass
    
    @abstractmethod
    def search_documents(self,
                        index_name: str,
                        search_text: Optional[str] = None,
                        search_vector: Optional[List[float]] = None,
                        filter_expression: Optional[str] = None,
                        select_fields: Optional[List[str]] = None,
                        top: int = 10,
                        skip: int = 0) -> Dict[str, Any]:
        """
        Search documents using text and/or vector search.
        
        Args:
            index_name: Name of the index
            search_text: Optional text query
            search_vector: Optional vector for similarity search
            filter_expression: Optional OData filter
            select_fields: Fields to return
            top: Maximum results to return
            skip: Number of results to skip
            
        Returns:
            Dict containing search results and metadata
            
        Raises:
            AzureSearchError: If search fails
        """
        pass
    
    @abstractmethod
    def hybrid_search(self,
                     index_name: str,
                     search_text: str,
                     search_vector: List[float],
                     filter_expression: Optional[str] = None,
                     top: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining text and vector search.
        
        Args:
            index_name: Name of the index
            search_text: Text query
            search_vector: Vector for similarity search
            filter_expression: Optional OData filter
            top: Maximum results to return
            
        Returns:
            List of search results with combined scores
            
        Raises:
            AzureSearchError: If search fails
        """
        pass
    
    @abstractmethod
    def get_document(self,
                    index_name: str,
                    document_key: str,
                    select_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by key.
        
        Args:
            index_name: Name of the index
            document_key: Document key
            select_fields: Optional fields to return
            
        Returns:
            Document if found, None otherwise
            
        Raises:
            AzureSearchError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def update_document(self,
                       index_name: str,
                       document: Dict[str, Any],
                       merge: bool = True) -> bool:
        """
        Update a document in the index.
        
        Args:
            index_name: Name of the index
            document: Document with updates
            merge: Whether to merge or replace
            
        Returns:
            True if update successful
            
        Raises:
            AzureSearchError: If update fails
        """
        pass
    
    @abstractmethod
    def delete_document(self,
                       index_name: str,
                       document_key: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            index_name: Name of the index
            document_key: Document key to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            AzureSearchError: If deletion fails
        """
        pass
    
    @abstractmethod
    def get_index_statistics(self, index_name: str) -> Dict[str, Any]:
        """
        Get statistics for an index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dict containing document count and storage size
            
        Raises:
            AzureSearchError: If retrieval fails
        """
        pass