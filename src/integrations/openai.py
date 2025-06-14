from openai import OpenAI
from typing import List
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for given text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise Exception(f"Embedding generation failed: {str(e)}")

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise Exception(f"Batch embedding generation failed: {str(e)}")


# Global instance
openai_client = OpenAIClient()
