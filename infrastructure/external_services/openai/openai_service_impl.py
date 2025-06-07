"""
OpenAI Service Implementation

Concrete implementation of AI services using OpenAI.
"""

from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
from infrastructure.external_services.openai.client import IOpenAIClient
from application.decorators.retry import retry
from application.decorators.circuit_breaker import circuit_breaker
from application.exceptions.infrastructure_exceptions import ExternalServiceException
from typing import List
import logging

logger = logging.getLogger(__name__)


class OpenAIServiceImpl(IEmbeddingService, ICompletionService):
    """
    OpenAI implementation of AI services.
    
    Provides embedding generation and text completion using OpenAI API.
    """
    
    def __init__(self, client: IOpenAIClient):
        self.client = client
        self.embedding_model = "text-embedding-ada-002"
        self.completion_model = "gpt-4"
    
    @retry(max_attempts=3, backoff_seconds=2)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for text using OpenAI.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            ExternalServiceException: If embedding creation fails
        """
        try:
            logger.debug(f"Creating embedding for text (length: {len(text)})")
            
            if not text.strip():
                raise ExternalServiceException("Cannot create embedding for empty text")
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text.strip()
            )
            
            if not response.data or len(response.data) == 0:
                raise ExternalServiceException("OpenAI returned no embedding data")
            
            embedding = response.data[0].embedding
            logger.debug(f"Successfully created embedding (dimension: {len(embedding)})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            if isinstance(e, ExternalServiceException):
                raise
            
            raise ExternalServiceException(f"Embedding creation failed: {str(e)}")
    
    @retry(max_attempts=3, backoff_seconds=2)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts using OpenAI.
        
        Args:
            texts: List of texts to create embeddings for
            
        Returns:
            List of embedding vectors
            
        Raises:
            ExternalServiceException: If embedding creation fails
        """
        try:
            logger.debug(f"Creating embeddings for {len(texts)} texts")
            
            if not texts:
                return []
            
            # Filter out empty texts
            non_empty_texts = [text.strip() for text in texts if text.strip()]
            if not non_empty_texts:
                raise ExternalServiceException("Cannot create embeddings for empty texts")
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=non_empty_texts
            )
            
            if not response.data or len(response.data) != len(non_empty_texts):
                raise ExternalServiceException(
                    f"OpenAI returned {len(response.data) if response.data else 0} embeddings "
                    f"for {len(non_empty_texts)} texts"
                )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Successfully created {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding creation failed: {e}")
            if isinstance(e, ExternalServiceException):
                raise
            
            raise ExternalServiceException(f"Batch embedding creation failed: {str(e)}")
    
    @retry(max_attempts=3, backoff_seconds=2)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def complete(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate completion for prompt using OpenAI.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated completion text
            
        Raises:
            ExternalServiceException: If completion fails
        """
        try:
            logger.debug(f"Generating completion for prompt (length: {len(prompt)})")
            
            if not prompt.strip():
                raise ExternalServiceException("Cannot generate completion for empty prompt")
            
            response = await self.client.chat.completions.create(
                model=self.completion_model,
                messages=[{"role": "user", "content": prompt.strip()}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if not response.choices or len(response.choices) == 0:
                raise ExternalServiceException("OpenAI returned no completion choices")
            
            content = response.choices[0].message.content
            if content is None:
                raise ExternalServiceException("OpenAI returned empty completion content")
            
            logger.debug(f"Successfully generated completion (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Completion failed: {e}")
            if isinstance(e, ExternalServiceException):
                raise
            
            raise ExternalServiceException(f"Completion failed: {str(e)}")
    
    @retry(max_attempts=3, backoff_seconds=2)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def complete_with_system(self, system: str, user: str, max_tokens: int = 100) -> str:
        """
        Generate completion with system message using OpenAI.
        
        Args:
            system: System message to set context
            user: User message/prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated completion text
            
        Raises:
            ExternalServiceException: If completion fails
        """
        try:
            logger.debug(f"Generating completion with system message (system: {len(system)}, user: {len(user)})")
            
            if not user.strip():
                raise ExternalServiceException("Cannot generate completion for empty user message")
            
            messages = []
            if system.strip():
                messages.append({"role": "system", "content": system.strip()})
            messages.append({"role": "user", "content": user.strip()})
            
            response = await self.client.chat.completions.create(
                model=self.completion_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if not response.choices or len(response.choices) == 0:
                raise ExternalServiceException("OpenAI returned no completion choices")
            
            content = response.choices[0].message.content
            if content is None:
                raise ExternalServiceException("OpenAI returned empty completion content")
            
            logger.debug(f"Successfully generated completion with system message (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Completion with system message failed: {e}")
            if isinstance(e, ExternalServiceException):
                raise
            
            raise ExternalServiceException(f"Completion with system message failed: {str(e)}")