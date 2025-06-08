"""
Custom role creation use case.

Handles creation of new custom roles from job descriptions.
"""

import logging

from core.exceptions import (
    ValidationError,
    BusinessLogicError
)
from domains.authentication.models.role import JobDescription, Role
from domains.shared.repositories.interfaces import IRoleRepository
from domains.onboarding.repositories.interfaces import IIndustryRepository
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
        role_repository: IRoleRepository,
        industry_repository: IIndustryRepository,
        search_client: IAzureCognitiveSearchClient,
        ai_client: IOpenAIClient
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            role_repository: Repository for role data operations
            industry_repository: Repository for industry data operations
            search_client: Azure Search client for indexing
            ai_client: OpenAI client for AI enhancements
        """
        self.role_repository = role_repository
        self.industry_repository = industry_repository
        self.search_client = search_client
        self.ai_client = ai_client
    
    async def execute(
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
            
            # Create role using repository
            role = Role(
                title=job_description.title,
                description=rewritten_description,
                industry_id=industry_id,
                search_keywords=','.join(generated_keywords) if isinstance(generated_keywords, list) else generated_keywords,
                hierarchy_level=job_description.hierarchy_level,
                is_active=True,
                created_by=created_by_user_id
            )
            
            try:
                created_role = await self.role_repository.save(role)
                if not created_role:
                    raise BusinessLogicError("Failed to create role in database")
            except Exception as e:
                logger.error(f"Database role creation failed: {str(e)}")
                raise BusinessLogicError(f"Failed to create role: {str(e)}")
            
            role = created_role
            
            # Add role to Azure Search index (non-blocking)
            try:
                # Get industry name for search indexing
                industry = await self.industry_repository.find_by_id(industry_id)
                industry_name = industry.get('name', '') if industry else ''
                
                search_doc = {
                    'id': role.id,
                    'title': role.title,
                    'description': role.description,
                    'industry_name': industry_name,
                    'search_keywords': role.search_keywords,
                    'hierarchy_level': role.hierarchy_level.value
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