import os
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
from django.conf import settings
from decouple import config
import logging

from core.interfaces import EmbeddingServiceInterface, LLMServiceInterface
from core.exceptions import ValidationError, BusinessLogicError
from authentication.models.role import JobDescription

logger = logging.getLogger(__name__)


class AzureOpenAIService(EmbeddingServiceInterface, LLMServiceInterface):
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
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text (implements EmbeddingServiceInterface).
        """
        try:
            if not text or not text.strip():
                raise ValidationError("Text cannot be empty")
            
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text.strip()
            )
            
            if response and response.data and len(response.data) > 0:
                return response.data[0].embedding
            else:
                raise BusinessLogicError('No embedding data returned from Azure OpenAI')
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Azure OpenAI embedding generation failed: {str(e)}")
            raise BusinessLogicError(f'Azure OpenAI embedding error: {str(e)}')
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Legacy method - get embedding vector for a given text.
        Kept for backward compatibility.
        """
        return self.generate_embedding(text)
    
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
    
    def generate_role_embedding(self, role_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for role data (implements EmbeddingServiceInterface).
        """
        embedding_text = self.get_role_embedding_text(role_data)
        return self.generate_embedding(embedding_text)
    
    def generate_job_embedding(self, job_description: JobDescription) -> List[float]:
        """
        Generate embedding for job description (implements EmbeddingServiceInterface).
        """
        # Create comprehensive text from job description
        embedding_text = f"Job Title: {job_description.title}\n"
        embedding_text += f"Level: {job_description.hierarchy_level.value}\n"
        embedding_text += f"Description: {job_description.description}\n"
        
        if job_description.requirements:
            embedding_text += f"Requirements: {job_description.requirements}\n"
        
        if job_description.responsibilities:
            embedding_text += f"Responsibilities: {job_description.responsibilities}"
        
        return self.generate_embedding(embedding_text)
    
    def embed_role(self, role_data: Dict[str, Any]) -> List[float]:
        """
        Legacy method - generate embedding for a role.
        Kept for backward compatibility.
        """
        return self.generate_role_embedding(role_data)
    
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
    
    def rewrite_role_description(
        self, 
        original_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Rewrite role description for clarity and engagement (implements LLMServiceInterface).
        """
        try:
            job_title = context.get('job_title', 'Role') if context else 'Role'
            
            prompt = f"""IMPORTANT: Rewrite this job description from first-person ("I do...") to third-person ("This role involves...").

Job Title: {job_title}

Original Description (first-person):
{original_description}

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
                if rewritten_description == original_description:
                    rewritten_description = self._basic_first_to_third_person(original_description)
                
                return rewritten_description
            else:
                # Fallback: return basic conversion if LLM fails
                return self._basic_first_to_third_person(original_description)
                
        except Exception as e:
            logger.error(f"Role description rewriting failed: {str(e)}")
            # Fallback: return basic conversion if LLM fails
            return self._basic_first_to_third_person(original_description)
    
    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze job description and extract key information (implements LLMServiceInterface).
        """
        try:
            prompt = f"""Analyze this job description and extract key information in JSON format:

Job Description:
{job_description}

Please extract:
- Required skills (technical and soft skills)
- Experience level (entry, mid, senior, executive)
- Industry keywords
- Key responsibilities
- Required qualifications

Provide the response in JSON format with keys: skills, experience_level, industry_keywords, responsibilities, qualifications"""

            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert job analyst. Extract structured information from job descriptions and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                analysis_text = response.choices[0].message.content.strip()
                try:
                    import json
                    return json.loads(analysis_text)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self._basic_job_analysis(job_description)
            else:
                return self._basic_job_analysis(job_description)
                
        except Exception as e:
            logger.error(f"Job description analysis failed: {str(e)}")
            return self._basic_job_analysis(job_description)
    
    def generate_role_suggestions(
        self, 
        job_title: str, 
        job_description: str,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate role suggestions based on job input (implements LLMServiceInterface).
        """
        try:
            industry_context = f" in the {industry} industry" if industry else ""
            
            prompt = f"""Based on this job title and description{industry_context}, suggest 3-5 similar or related roles that might be relevant.

Job Title: {job_title}
Job Description: {job_description}
{f"Industry: {industry}" if industry else ""}

For each suggestion, provide:
- Role title
- Brief description (2-3 sentences)
- Key differences from the original role
- Seniority level

Provide response in JSON format as an array of objects with keys: title, description, differences, seniority_level"""

            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert career advisor. Generate relevant role suggestions based on job descriptions and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            if response and response.choices and len(response.choices) > 0:
                suggestions_text = response.choices[0].message.content.strip()
                try:
                    import json
                    return json.loads(suggestions_text)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self._basic_role_suggestions(job_title, industry)
            else:
                return self._basic_role_suggestions(job_title, industry)
                
        except Exception as e:
            logger.error(f"Role suggestions generation failed: {str(e)}")
            return self._basic_role_suggestions(job_title, industry)
    
    def rewrite_job_description(self, job_title: str, job_description: str) -> str:
        """
        Legacy method - rewrite job description from first person to third person.
        Kept for backward compatibility.
        """
        return self.rewrite_role_description(job_description, {'job_title': job_title})
    
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
    
    def _basic_job_analysis(self, job_description: str) -> Dict[str, Any]:
        """Basic fallback method for job analysis."""
        words = job_description.lower().split()
        
        # Extract basic skills based on common keywords
        tech_skills = []
        for word in words:
            if any(tech in word for tech in ['python', 'java', 'sql', 'react', 'aws', 'azure', 'docker']):
                tech_skills.append(word)
        
        # Determine experience level based on keywords
        experience_level = "mid"
        if any(word in job_description.lower() for word in ['senior', 'lead', 'principal', 'architect']):
            experience_level = "senior"
        elif any(word in job_description.lower() for word in ['junior', 'entry', 'trainee', 'graduate']):
            experience_level = "entry"
        elif any(word in job_description.lower() for word in ['director', 'vp', 'chief', 'head of']):
            experience_level = "executive"
        
        return {
            "skills": tech_skills[:10],
            "experience_level": experience_level,
            "industry_keywords": [],
            "responsibilities": [],
            "qualifications": []
        }
    
    def _basic_role_suggestions(self, job_title: str, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """Basic fallback method for role suggestions."""
        suggestions = []
        
        # Generate basic suggestions based on job title
        if "engineer" in job_title.lower():
            suggestions.append({
                "title": "Senior Software Engineer",
                "description": "Advanced technical role with increased responsibilities and mentoring duties.",
                "differences": "Higher seniority level with leadership expectations",
                "seniority_level": "senior"
            })
        
        if "analyst" in job_title.lower():
            suggestions.append({
                "title": "Data Scientist",
                "description": "Advanced analytics role focusing on machine learning and statistical modeling.",
                "differences": "More technical and focused on predictive modeling",
                "seniority_level": "mid"
            })
        
        # Add generic suggestions if no specific matches
        if not suggestions:
            suggestions.append({
                "title": f"Senior {job_title}",
                "description": f"Advanced version of {job_title} with additional responsibilities.",
                "differences": "Higher seniority and broader scope",
                "seniority_level": "senior"
            })
        
        return suggestions[:3]