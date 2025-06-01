import os
from openai import AzureOpenAI
from typing import List, Dict, Any
from django.conf import settings
from decouple import config


class AzureOpenAIService:
    """
    Service class for interacting with Azure OpenAI embeddings
    """
    
    def __init__(self):
        # Configure Azure OpenAI client using v1.0+ API
        self.client = AzureOpenAI(
            azure_endpoint=config('AZURE_OPENAI_ENDPOINT'),
            api_key=config('AZURE_OPENAI_API_KEY'),
            api_version=config('AZURE_OPENAI_API_VERSION')
        )
        self.embedding_deployment = config('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for a given text using Azure OpenAI
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )
            
            if response and response.data and len(response.data) > 0:
                return response.data[0].embedding
            else:
                raise Exception('No embedding data returned from Azure OpenAI')
                
        except Exception as e:
            raise Exception(f'Azure OpenAI embedding error: {str(e)}')
    
    def get_role_embedding_text(self, role_data: Dict[str, Any]) -> str:
        """
        Create a comprehensive text representation of a role for embedding
        """
        title = role_data.get('title', '')
        description = role_data.get('description', '')
        hierarchy_level = role_data.get('hierarchy_level', '')
        search_keywords = role_data.get('search_keywords', [])
        industry_name = role_data.get('industry_name', '')
        
        # Create a comprehensive text for embedding
        embedding_text = f"Job Title: {title}\n"
        embedding_text += f"Industry: {industry_name}\n"
        embedding_text += f"Level: {hierarchy_level}\n"
        embedding_text += f"Description: {description}\n"
        
        if search_keywords:
            keywords_text = ", ".join(search_keywords)
            embedding_text += f"Key Skills: {keywords_text}"
        
        return embedding_text
    
    def embed_role(self, role_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a role based on its comprehensive information
        """
        embedding_text = self.get_role_embedding_text(role_data)
        return self.get_embedding(embedding_text)