"""
OpenAI Client Interface

Defines the contract for OpenAI API client implementation.
This interface abstracts OpenAI-specific operations for LLM and embedding services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncIterator
from enum import Enum


class OpenAIModel(Enum):
    """Available OpenAI models."""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"


class IOpenAIClient(ABC):
    """
    OpenAI client interface for LLM and embedding operations.
    
    This interface provides access to OpenAI's completion, chat, and embedding APIs.
    """
    
    @abstractmethod
    def create_completion(self, 
                         prompt: str,
                         model: str = OpenAIModel.GPT_35_TURBO.value,
                         max_tokens: Optional[int] = None,
                         temperature: float = 0.7,
                         top_p: float = 1.0,
                         frequency_penalty: float = 0.0,
                         presence_penalty: float = 0.0,
                         stop: Optional[List[str]] = None) -> str:
        """
        Create a text completion.
        
        Args:
            prompt: The prompt to complete
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            stop: Stop sequences
            
        Returns:
            Generated completion text
            
        Raises:
            OpenAIError: If completion fails
        """
        pass
    
    @abstractmethod
    def create_chat_completion(self,
                             messages: List[Dict[str, str]],
                             model: str = OpenAIModel.GPT_35_TURBO.value,
                             max_tokens: Optional[int] = None,
                             temperature: float = 0.7,
                             top_p: float = 1.0,
                             frequency_penalty: float = 0.0,
                             presence_penalty: float = 0.0,
                             functions: Optional[List[Dict[str, Any]]] = None,
                             function_call: Optional[Union[str, Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            functions: Optional function definitions for function calling
            function_call: Controls function calling behavior
            
        Returns:
            Dict containing:
                - content: Generated message content
                - role: Message role (assistant)
                - function_call: Optional function call details
                - finish_reason: Reason for completion
                
        Raises:
            OpenAIError: If chat completion fails
        """
        pass
    
    @abstractmethod
    async def create_chat_completion_stream(self,
                                          messages: List[Dict[str, str]],
                                          model: str = OpenAIModel.GPT_35_TURBO.value,
                                          max_tokens: Optional[int] = None,
                                          temperature: float = 0.7,
                                          top_p: float = 1.0) -> AsyncIterator[str]:
        """
        Create a streaming chat completion.
        
        Args:
            messages: List of message objects
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Yields:
            Chunks of generated text
            
        Raises:
            OpenAIError: If streaming fails
        """
        pass
    
    @abstractmethod
    def create_embedding(self,
                        text: str,
                        model: str = OpenAIModel.TEXT_EMBEDDING_ADA_002.value) -> List[float]:
        """
        Create an embedding vector for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            Embedding vector
            
        Raises:
            OpenAIError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def create_embeddings(self,
                         texts: List[str],
                         model: str = OpenAIModel.TEXT_EMBEDDING_ADA_002.value) -> List[List[float]]:
        """
        Create embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
            
        Raises:
            OpenAIError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str = OpenAIModel.GPT_35_TURBO.value) -> int:
        """
        Count tokens in text for a specific model.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def moderate_content(self, text: str) -> Dict[str, Any]:
        """
        Check content for policy violations using moderation API.
        
        Args:
            text: Text to moderate
            
        Returns:
            Dict containing:
                - flagged: Whether content was flagged
                - categories: Dict of category flags
                - category_scores: Dict of category scores
                
        Raises:
            OpenAIError: If moderation fails
        """
        pass


class IOpenAIAssistantClient(ABC):
    """
    OpenAI Assistant API client interface.
    
    Provides operations for managing and using OpenAI Assistants.
    """
    
    @abstractmethod
    def create_assistant(self,
                        name: str,
                        instructions: str,
                        model: str = OpenAIModel.GPT_4_TURBO.value,
                        tools: Optional[List[Dict[str, Any]]] = None,
                        file_ids: Optional[List[str]] = None) -> str:
        """
        Create a new assistant.
        
        Args:
            name: Assistant name
            instructions: System instructions for the assistant
            model: Model to use
            tools: List of tools (e.g., code_interpreter, retrieval)
            file_ids: List of file IDs for the assistant
            
        Returns:
            Assistant ID
            
        Raises:
            OpenAIError: If creation fails
        """
        pass
    
    @abstractmethod
    def create_thread(self, messages: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Create a new conversation thread.
        
        Args:
            messages: Optional initial messages
            
        Returns:
            Thread ID
            
        Raises:
            OpenAIError: If creation fails
        """
        pass
    
    @abstractmethod
    def add_message_to_thread(self,
                            thread_id: str,
                            content: str,
                            role: str = "user",
                            file_ids: Optional[List[str]] = None) -> str:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread ID
            content: Message content
            role: Message role (user/assistant)
            file_ids: Optional file attachments
            
        Returns:
            Message ID
            
        Raises:
            OpenAIError: If adding fails
        """
        pass
    
    @abstractmethod
    def run_assistant(self,
                     thread_id: str,
                     assistant_id: str,
                     instructions: Optional[str] = None) -> str:
        """
        Run an assistant on a thread.
        
        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID
            instructions: Optional additional instructions
            
        Returns:
            Run ID
            
        Raises:
            OpenAIError: If run fails
        """
        pass
    
    @abstractmethod
    def get_run_status(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Get the status of an assistant run.
        
        Args:
            thread_id: Thread ID
            run_id: Run ID
            
        Returns:
            Dict containing run status and details
            
        Raises:
            OpenAIError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def get_thread_messages(self,
                          thread_id: str,
                          limit: Optional[int] = None,
                          order: str = "desc") -> List[Dict[str, Any]]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum messages to retrieve
            order: Sort order (asc/desc)
            
        Returns:
            List of messages
            
        Raises:
            OpenAIError: If retrieval fails
        """
        pass


class IOpenAIFileClient(ABC):
    """
    OpenAI File API client interface.
    
    Provides operations for uploading and managing files.
    """
    
    @abstractmethod
    def upload_file(self, file_path: str, purpose: str = "assistants") -> str:
        """
        Upload a file to OpenAI.
        
        Args:
            file_path: Path to file to upload
            purpose: Purpose of file (assistants, fine-tune)
            
        Returns:
            File ID
            
        Raises:
            OpenAIError: If upload fails
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from OpenAI.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            OpenAIError: If deletion fails
        """
        pass
    
    @abstractmethod
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_id: File ID
            
        Returns:
            File information
            
        Raises:
            OpenAIError: If retrieval fails
        """
        pass