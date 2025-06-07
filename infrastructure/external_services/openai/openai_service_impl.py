"""
OpenAI Service Implementation

Concrete implementation of AI services using OpenAI.
"""

from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
from infrastructure.external_services.openai.client import IOpenAIClient
from application.decorators.retry import retry
from application.decorators.circuit_breaker import circuit_breaker
from application.exceptions.infrastructure_exceptions import (
    ExternalServiceException,
    AIServiceException
)
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
            AIServiceException: If embedding creation fails
        """
        try:
            logger.debug(f"Creating embedding for text (length: {len(text)})")
            
            if not text.strip():
                raise AIServiceException(
                    "Cannot create embedding for empty text",
                    model=self.embedding_model,
                    operation="create_embedding"
                )
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text.strip()
            )
            
            if not response.data or len(response.data) == 0:
                raise AIServiceException(
                    "OpenAI returned no embedding data",
                    model=self.embedding_model,
                    operation="create_embedding"
                )
            
            embedding = response.data[0].embedding
            logger.debug(f"Successfully created embedding (dimension: {len(embedding)})")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            if isinstance(e, AIServiceException):
                raise
            
            raise AIServiceException(
                f"Embedding creation failed: {str(e)}",
                model=self.embedding_model,
                operation="create_embedding",
                original_exception=e,
                context={"text_length": len(text)}
            )
    
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
            AIServiceException: If embedding creation fails
        """
        try:
            logger.debug(f"Creating embeddings for {len(texts)} texts")
            
            if not texts:
                return []
            
            # Filter out empty texts
            non_empty_texts = [text.strip() for text in texts if text.strip()]
            if not non_empty_texts:
                raise AIServiceException(
                    "Cannot create embeddings for empty texts",
                    model=self.embedding_model,
                    operation="create_embeddings"
                )
            
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=non_empty_texts
            )
            
            if not response.data or len(response.data) != len(non_empty_texts):
                raise AIServiceException(
                    f"OpenAI returned {len(response.data) if response.data else 0} embeddings "
                    f"for {len(non_empty_texts)} texts",
                    model=self.embedding_model,
                    operation="create_embeddings"
                )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Successfully created {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding creation failed: {e}")
            if isinstance(e, AIServiceException):
                raise
            
            raise AIServiceException(
                f"Batch embedding creation failed: {str(e)}",
                model=self.embedding_model,
                operation="create_embeddings",
                original_exception=e,
                context={"text_count": len(texts)}
            )
    
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
            AIServiceException: If completion fails
        """
        try:
            logger.debug(f"Generating completion for prompt (length: {len(prompt)})")
            
            if not prompt.strip():
                raise AIServiceException(
                    "Cannot generate completion for empty prompt",
                    model=self.completion_model,
                    operation="complete"
                )
            
            response = await self.client.chat.completions.create(
                model=self.completion_model,
                messages=[{"role": "user", "content": prompt.strip()}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if not response.choices or len(response.choices) == 0:
                raise AIServiceException(
                    "OpenAI returned no completion choices",
                    model=self.completion_model,
                    operation="complete"
                )
            
            content = response.choices[0].message.content
            if content is None:
                raise AIServiceException(
                    "OpenAI returned empty completion content",
                    model=self.completion_model,
                    operation="complete"
                )
            
            logger.debug(f"Successfully generated completion (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Completion failed: {e}")
            if isinstance(e, AIServiceException):
                raise
            
            raise AIServiceException(
                f"Completion failed: {str(e)}",
                model=self.completion_model,
                operation="complete",
                original_exception=e,
                context={"prompt_length": len(prompt), "max_tokens": max_tokens}
            )
    
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
            AIServiceException: If completion fails
        """
        try:
            logger.debug(f"Generating completion with system message (system: {len(system)}, user: {len(user)})")
            
            if not user.strip():
                raise AIServiceException(
                    "Cannot generate completion for empty user message",
                    model=self.completion_model,
                    operation="complete_with_system"
                )
            
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
                raise AIServiceException(
                    "OpenAI returned no completion choices",
                    model=self.completion_model,
                    operation="complete_with_system"
                )
            
            content = response.choices[0].message.content
            if content is None:
                raise AIServiceException(
                    "OpenAI returned empty completion content",
                    model=self.completion_model,
                    operation="complete_with_system"
                )
            
            logger.debug(f"Successfully generated completion with system message (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Completion with system message failed: {e}")
            if isinstance(e, AIServiceException):
                raise
            
            raise AIServiceException(
                f"Completion with system message failed: {str(e)}",
                model=self.completion_model,
                operation="complete_with_system",
                original_exception=e,
                context={
                    "system_length": len(system),
                    "user_length": len(user),
                    "max_tokens": max_tokens
                }
            )