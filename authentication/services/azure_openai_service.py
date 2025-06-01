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
        self.chat_deployment = config('AZURE_OPENAI_CHAT_DEPLOYMENT', default='gpt-4o')
    
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
    
    def generate_role_keywords(self, job_title: str, job_description: str) -> List[str]:
        """
        Generate relevant keywords for a role using GPT-4o based on job title and description
        """
        try:
            prompt = f"""Based on the following job title and description, generate 5-8 relevant keywords that best represent the key skills, technologies, and competencies required for this role.

Job Title: {job_title}
Job Description: {job_description}

Please provide only the keywords separated by commas, focusing on:
- Technical skills and tools
- Core competencies 
- Industry-specific knowledge
- Soft skills relevant to the role

Keywords:"""

            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are a professional HR expert specialized in job analysis and skill identification."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            if response and response.choices and len(response.choices) > 0:
                keywords_text = response.choices[0].message.content.strip()
                # Parse keywords from response
                keywords = [keyword.strip() for keyword in keywords_text.split(',')]
                # Filter out empty keywords and limit to 8 max
                keywords = [kw for kw in keywords if kw and len(kw) > 1][:8]
                return keywords
            else:
                # Fallback keywords if LLM fails
                return [job_title.lower().replace(' ', '_')]
                
        except Exception as e:
            # Fallback to basic keywords if LLM fails
            basic_keywords = job_title.lower().split()
            return [kw for kw in basic_keywords if len(kw) > 2][:5]
    
    def rewrite_job_description(self, job_title: str, job_description: str) -> str:
        """
        Rewrite job description from first person to third person using GPT-4o
        """
        try:
            prompt = f"""IMPORTANT: Rewrite this job description from first-person ("I do...") to third-person ("This role involves...").

Job Title: {job_title}

Original Description (first-person):
{job_description}

INSTRUCTIONS:
- Change ALL "I" statements to third-person
- Change "I analyze" to "Analyzes" or "This role involves analyzing"
- Change "I work with" to "Works with" or "Utilizes" 
- Change "I manage" to "Manages" or "Responsible for managing"
- Change "I create" to "Creates" or "Develops"
- Keep all technical details and responsibilities
- Make it sound professional for a job database

Rewritten Description (third-person):"""

            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert HR writer. You MUST convert first-person job descriptions to third-person format. Change every 'I do X' to 'Does X' or 'Responsible for X'."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                rewritten_description = response.choices[0].message.content.strip()
                # Remove any quotation marks that might be added by the LLM
                rewritten_description = rewritten_description.strip('"').strip("'")
                
                # Fallback: if LLM didn't change anything, do basic find/replace
                if rewritten_description == job_description:
                    rewritten_description = self._basic_first_to_third_person(job_description)
                
                return rewritten_description
            else:
                # Fallback: return basic conversion if LLM fails
                return self._basic_first_to_third_person(job_description)
                
        except Exception as e:
            # Fallback: return basic conversion if LLM fails
            return self._basic_first_to_third_person(job_description)
    
    def _basic_first_to_third_person(self, description: str) -> str:
        """
        Basic fallback method to convert first person to third person
        """
        # Simple replacements as fallback
        replacements = [
            (" I analyze ", " Analyzes "),
            (" I work ", " Works "),
            (" I manage ", " Manages "),
            (" I create ", " Creates "),
            (" I develop ", " Develops "),
            (" I handle ", " Handles "),
            (" I oversee ", " Oversees "),
            (" I collaborate ", " Collaborates "),
            (" I also ", " Also "),
            (" I track ", " Tracks "),
            (" I report ", " Reports "),
            ("I analyze", "Analyzes"),
            ("I work", "Works"),
            ("I manage", "Manages"),
            ("I create", "Creates"),
            ("I develop", "Develops"),
            ("I handle", "Handles"),
            ("I oversee", "Oversees"),
            ("I collaborate", "Collaborates"),
            ("I track", "Tracks"),
            ("I report", "Reports")
        ]
        
        result = description
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result