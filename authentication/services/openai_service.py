import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from django.conf import settings
from decouple import config
import logging
from tenacity import retry, wait_random_exponential, stop_after_attempt

from core.interfaces import EmbeddingServiceInterface, LLMServiceInterface
from core.exceptions import ValidationError, BusinessLogicError
from authentication.models.role import JobDescription

logger = logging.getLogger(__name__)


class OpenAIService(EmbeddingServiceInterface, LLMServiceInterface):
    """
    Service class for interacting with OpenAI embeddings and language models
    """
    
    def __init__(self):
        # Get OpenAI API key from environment
        api_key = config('OPENAI_API_KEY', default=None)
        
        if not api_key:
            logger.warning("OPENAI_API_KEY not configured")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = config('OPENAI_CHAT_MODEL', default='gpt-4o-mini')
        
        logger.info(f"OpenAI config: client_available={self.client is not None}, embedding_model={self.embedding_model}")
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text with retry logic (implements EmbeddingServiceInterface).
        """
        try:
            if not text or not text.strip():
                raise ValidationError("Text cannot be empty")
            
            # Check if client is available
            if not self.client:
                logger.warning("OpenAI client not available, using fallback embedding")
                return self._generate_fallback_embedding(text)
            
            logger.info(f"Generating embedding for text: {text[:50]}...")
            
            response = self.client.embeddings.create(
                input=text.strip(),
                model=self.embedding_model
            )
            
            if response and response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                logger.info(f"Successfully generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                raise BusinessLogicError('No embedding data returned from OpenAI')
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Instead of failing completely, return a fallback dummy embedding
            logger.warning("Falling back to dummy embedding vector for development")
            return self._generate_fallback_embedding(text)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Generate a fallback embedding when OpenAI is unavailable.
        This creates a simple hash-based embedding for development/testing.
        """
        import hashlib
        import struct
        
        # Create a deterministic hash of the text
        text_hash = hashlib.md5(text.encode()).digest()
        
        # Convert hash to 1536 float values (matching OpenAI embedding dimensions)
        embedding = []
        for i in range(0, len(text_hash), 4):
            # Convert 4 bytes to float
            if i + 4 <= len(text_hash):
                val = struct.unpack('f', text_hash[i:i+4])[0]
            else:
                val = 0.0
            embedding.append(val)
        
        # Pad to 1536 dimensions
        while len(embedding) < 1536:
            embedding.append(0.0)
        
        # Truncate to exactly 1536 dimensions
        embedding = embedding[:1536]
        
        logger.info(f"Generated fallback embedding with {len(embedding)} dimensions")
        return embedding
    
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
        
        if job_description.industry:
            embedding_text += f"Industry: {job_description.industry}\n"
        
        if job_description.required_skills:
            embedding_text += f"Required Skills: {', '.join(job_description.required_skills)}\n"
        
        if job_description.preferred_skills:
            embedding_text += f"Preferred Skills: {', '.join(job_description.preferred_skills)}"
        
        return self.generate_embedding(embedding_text)
    
    def embed_role(self, role_data: Dict[str, Any]) -> List[float]:
        """
        Legacy method - generate embedding for a role.
        Kept for backward compatibility.
        """
        return self.generate_role_embedding(role_data)
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def generate_role_keywords(self, job_title: str, job_description: str) -> List[str]:
        """
        Generate relevant keywords for a role using GPT based on job title and description
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not available, generating basic keywords")
                return self._generate_basic_keywords(job_title, job_description)

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
                model=self.chat_model,
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
                return self._generate_basic_keywords(job_title, job_description)
                
        except Exception as e:
            logger.error(f"OpenAI keyword generation failed: {str(e)}")
            # Fallback to basic keywords if LLM fails
            return self._generate_basic_keywords(job_title, job_description)
    
    def _generate_basic_keywords(self, job_title: str, job_description: str) -> List[str]:
        """Generate basic keywords from job title and description"""
        basic_keywords = job_title.lower().split()
        desc_keywords = job_description.lower().split()
        combined = basic_keywords + desc_keywords
        # Filter meaningful words (longer than 2 chars)
        keywords = [kw for kw in combined if len(kw) > 2][:5]
        return keywords
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def rewrite_role_description(
        self, 
        original_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Rewrite role description for clarity and engagement (implements LLMServiceInterface).
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not available, using basic conversion")
                return self._basic_first_to_third_person(original_description)

            job_title = context.get('job_title', 'Role') if context else 'Role'
            
            prompt = f"""CRITICAL: Convert this first-person job description to third-person. Return ONLY the rewritten description text with NO formatting, NO headers, NO markdown, NO title repetition.

Original Description: {original_description}

RULES:
1. Change "I analyze" → "Analyzes"
2. Change "I work with" → "Works with" 
3. Change "I manage" → "Manages"
4. Change "I create" → "Creates"
5. Change "I develop" → "Develops"
6. Keep all technical details exactly as they are
7. DO NOT add any markdown formatting (**bold**, headers, etc.)
8. DO NOT repeat the job title
9. DO NOT add "Job Title:" or "Description:" labels
10. Return ONLY the plain description text

Third-person description:"""

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are an expert HR writer. Convert first-person job descriptions to third-person format. Return ONLY the plain text description with NO markdown, NO formatting, NO headers, NO job title repetition. Just the converted description text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                rewritten_description = response.choices[0].message.content.strip()
                
                # Clean up any formatting that might have been added
                rewritten_description = self._clean_description_formatting(rewritten_description)
                
                # Fallback: if LLM didn't change anything, do basic find/replace
                if rewritten_description == original_description:
                    rewritten_description = self._basic_first_to_third_person(original_description)
                
                return rewritten_description
            else:
                # Fallback: return basic conversion if LLM fails
                return self._basic_first_to_third_person(original_description)
                
        except Exception as e:
            logger.error(f"OpenAI role description rewriting failed: {str(e)}")
            # Fallback: return basic conversion if LLM fails
            return self._basic_first_to_third_person(original_description)
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """
        Analyze job description and extract key information (implements LLMServiceInterface).
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not available, using basic analysis")
                return self._basic_job_analysis(job_description)

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
                model=self.chat_model,
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
            logger.error(f"OpenAI job description analysis failed: {str(e)}")
            return self._basic_job_analysis(job_description)
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
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
            if not self.client:
                logger.warning("OpenAI client not available, using basic suggestions")
                return self._basic_role_suggestions(job_title, industry)

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
                model=self.chat_model,
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
            logger.error(f"OpenAI role suggestions generation failed: {str(e)}")
            return self._basic_role_suggestions(job_title, industry)
    
    def rewrite_job_description(self, job_title: str, job_description: str) -> str:
        """
        Legacy method - rewrite job description from first person to third person.
        Kept for backward compatibility.
        """
        return self.rewrite_role_description(job_description, {'job_title': job_title})
    
    def _clean_description_formatting(self, description: str) -> str:
        """
        Clean unwanted formatting from LLM-generated descriptions
        """
        import re
        
        # Remove quotation marks
        description = description.strip('"').strip("'")
        
        # Remove markdown bold formatting
        description = re.sub(r'\*\*(.*?)\*\*', r'\1', description)
        
        # Remove markdown headers
        description = re.sub(r'^#+\s*', '', description, flags=re.MULTILINE)
        
        # Remove job title repetition patterns
        description = re.sub(r'^Job Title:\s*.*?\n', '', description, flags=re.MULTILINE)
        description = re.sub(r'^Description:\s*', '', description, flags=re.MULTILINE)
        description = re.sub(r'^\*\*Job Title:.*?\*\*\s*\n', '', description, flags=re.MULTILINE)
        description = re.sub(r'^\*\*Description:\*\*\s*\n', '', description, flags=re.MULTILINE)
        
        # Remove any lines that are just the job title repeated
        lines = description.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and lines that are just formatting
            if line and not re.match(r'^\*+$', line) and not re.match(r'^-+$', line):
                cleaned_lines.append(line)
        
        # Join lines back together
        result = '\n'.join(cleaned_lines).strip()
        
        # Replace multiple newlines with single newlines
        result = re.sub(r'\n\s*\n', '\n', result)
        
        return result
    
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