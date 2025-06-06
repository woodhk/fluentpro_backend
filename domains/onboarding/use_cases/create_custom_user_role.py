"""
Custom role creation use case.

Handles creation of new custom roles from job descriptions.
"""

import logging

from core.exceptions import (
    ValidationError,
    BusinessLogicError
)
from authentication.models.role import JobDescription, Role
from infrastructure.persistence.supabase.client import ISupabaseClient
from infrastructure.external_services.azure.client import IAzureCognitiveSearchClient
from infrastructure.external_services.openai.client import IOpenAIClient

logger = logging.getLogger(__name__)


class CreateCustomUserRole:
    """
    Use case for creating custom roles from job descriptions.
    
    Handles role creation with AI enhancement for description
    rewriting and keyword generation.
    """
    
    def __init__(
        self,
        database_client: ISupabaseClient,
        search_client: IAzureCognitiveSearchClient,
        ai_client: IOpenAIClient
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            database_client: Supabase client for data persistence
            search_client: Azure Search client for indexing
            ai_client: OpenAI client for AI enhancements
        """
        self.database_client = database_client
        self.search_client = search_client
        self.ai_client = ai_client
    
    def execute(
        self,
        job_description: JobDescription,
        industry_id: str,
        created_by_user_id: str
    ) -> Role:
        """
        Execute custom role creation.
        
        Args:
            job_description: Job description for the new role
            industry_id: Industry ID for the role
            created_by_user_id: User ID who created the role
            
        Returns:
            Created Role instance
            
        Raises:
            ValidationError: If job description is invalid
            BusinessLogicError: If role creation fails
        """
        try:
            # Validate job description
            if not job_description.title.strip():
                raise ValidationError("Job title is required")
            
            if not job_description.description.strip():
                raise ValidationError("Job description is required")
            
            # Rewrite description from first person to third person
            try:
                rewrite_prompt = f"Rewrite this job description from first person to third person professional format:\n\nTitle: {job_description.title}\nDescription: {job_description.description}"
                rewritten_description = self.ai_client.create_completion(rewrite_prompt)
            except Exception as e:
                logger.warning(f"Failed to rewrite job description, using original: {str(e)}")
                rewritten_description = job_description.description
            
            # Generate keywords using AI
            try:
                keywords_prompt = f"Generate relevant search keywords for this job role:\n\nTitle: {job_description.title}\nDescription: {job_description.description}\n\nProvide 5-10 keywords separated by commas:"
                keywords_response = self.ai_client.create_completion(keywords_prompt)
                generated_keywords = [k.strip() for k in keywords_response.split(',') if k.strip()]
            except Exception as e:
                logger.warning(f"Failed to generate keywords, using fallback: {str(e)}")
                from core.utils import generate_search_keywords
                generated_keywords = generate_search_keywords(
                    f"{job_description.title} {job_description.description}"
                )
            
            # Create role in database
            role_data = {
                'title': job_description.title,
                'description': rewritten_description,
                'industry_id': industry_id,
                'search_keywords': ','.join(generated_keywords) if isinstance(generated_keywords, list) else generated_keywords,
                'hierarchy_level': job_description.hierarchy_level.value,
                'is_active': True,
                'created_by': created_by_user_id
            }
            
            try:
                role_response = self.database_client.table('roles').insert(role_data).execute()
                if not role_response.data:
                    raise BusinessLogicError("Failed to create role in database")
                new_role_id = role_response.data[0]['id']
            except Exception as e:
                logger.error(f"Database role creation failed: {str(e)}")
                raise BusinessLogicError(f"Failed to create role: {str(e)}")
            
            # Get the complete role data with industry information
            role_with_industry_response = self.database_client.table('roles')\
                .select('*, industries(name)')\
                .eq('id', new_role_id)\
                .execute()
            
            if not role_with_industry_response.data:
                raise BusinessLogicError("Failed to retrieve created role")
            
            role_with_industry = role_with_industry_response.data[0]
            
            # Create Role instance
            role = Role.from_supabase_data(role_with_industry)
            
            # Add role to Azure Search index (non-blocking)
            try:
                search_doc = {
                    'id': role_with_industry['id'],
                    'title': role_with_industry['title'],
                    'description': role_with_industry['description'],
                    'industry_name': role_with_industry.get('industries', {}).get('name', ''),
                    'search_keywords': role_with_industry.get('search_keywords', ''),
                    'hierarchy_level': role_with_industry.get('hierarchy_level', 'associate')
                }
                
                search_result = self.search_client.upload_documents('roles', [search_doc])
                if not search_result.get('success'):
                    logger.warning(f"Failed to add role to search index: {search_result.get('error')}")
            except Exception as e:
                logger.warning(f"Failed to add role to search index: {str(e)}")
            
            return role
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Failed to create custom role: {str(e)}")
            raise BusinessLogicError(f"Failed to create custom role: {str(e)}")