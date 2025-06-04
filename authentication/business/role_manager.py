"""
Business logic for role and industry management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from core.exceptions import (
    BusinessLogicError,
    ValidationError,
    ResourceNotFoundError,
    AzureSearchError,
    AzureOpenAIError
)
from authentication.models.role import (
    Role, Industry, JobDescription, RoleMatch, 
    UserRoleSelection, RoleSource, HierarchyLevel
)
from authentication.services.supabase_service import SupabaseService
from authentication.services.azure_search_service import AzureSearchService
from authentication.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class RoleManager:
    """
    Business logic manager for role and industry operations.
    Handles role matching, creation, and industry management.
    """
    
    # Configuration constants
    MIN_RELEVANCY_SCORE = 0.7  # 70% minimum relevancy score - easy to change
    
    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        azure_search_service: Optional[AzureSearchService] = None,
        openai_service: Optional[OpenAIService] = None
    ):
        self.supabase_service = supabase_service or SupabaseService()
        self.azure_search_service = azure_search_service or AzureSearchService()
        self.openai_service = openai_service or OpenAIService()
    
    def find_matching_roles(
        self, 
        job_description: JobDescription,
        industry_filter: Optional[str] = None,
        max_results: int = 5
    ) -> List[RoleMatch]:
        """
        Find roles that match a job description.
        
        Args:
            job_description: Job description to match against
            industry_filter: Optional industry filter
            max_results: Maximum number of results to return
            
        Returns:
            List of RoleMatch instances sorted by relevance
            
        Raises:
            AzureOpenAIError: If embedding generation fails
            AzureSearchError: If search fails
        """
        try:
            # Generate embedding for job description
            try:
                query_embedding = self.openai_service.get_embedding(job_description.search_text)
            except Exception as e:
                logger.error(f"Failed to generate embedding for job search: {str(e)}")
                raise AzureOpenAIError(f"Failed to generate search embedding: {str(e)}")
            
            # Prepare search filters
            filters = None
            if industry_filter:
                filters = f"industry_name eq '{industry_filter}'"
            
            # Perform hybrid search
            try:
                search_result = self.azure_search_service.hybrid_search_roles(
                    text_query=f"{job_description.title} {job_description.description}",
                    query_embedding=query_embedding,
                    top_k=max_results,
                    filters=filters
                )
            except Exception as e:
                logger.error(f"Azure Search failed: {str(e)}")
                raise AzureSearchError(f"Role search failed: {str(e)}")
            
            if not search_result.get('success'):
                raise AzureSearchError(search_result.get('error', 'Unknown search error'))
            
            # Convert search results to RoleMatch instances and filter by relevancy
            role_matches = []
            for result in search_result.get('results', []):
                try:
                    # Skip results below minimum relevancy threshold
                    relevance_score = result['score']
                    if relevance_score < self.MIN_RELEVANCY_SCORE:
                        logger.debug(f"Skipping role '{result['title']}' with low relevancy score: {relevance_score:.3f}")
                        continue
                    
                    # Create Role instance from search result
                    role_data = {
                        'id': result['id'],
                        'title': result['title'],
                        'description': result['description'],
                        'industry_id': result.get('industry_id', ''),
                        'industry_name': result.get('industry_name', ''),
                        'hierarchy_level': result.get('hierarchy_level', 'associate'),
                        'search_keywords': result.get('search_keywords', '').split() if result.get('search_keywords') else [],
                        'is_active': True
                    }
                    
                    role = Role.from_supabase_data(role_data)
                    
                    # Create match reasons based on improved search results
                    match_reasons = []
                    if result.get('semantic_caption'):
                        match_reasons.append("Semantic content match")
                    if relevance_score > 0.9:
                        match_reasons.append("Excellent match")
                    elif relevance_score > 0.8:
                        match_reasons.append("High relevancy match")
                    elif relevance_score > 0.7:
                        match_reasons.append("Good relevancy match")
                    else:
                        match_reasons.append("Acceptable match")
                    
                    # Add specific match reasons based on query content
                    title_lower = result['title'].lower()
                    query_text = f"{job_description.title} {job_description.description}".lower()
                    if any(word in title_lower for word in job_description.title.lower().split()):
                        match_reasons.append("Title keyword match")
                    
                    role_match = RoleMatch(
                        role=role,
                        relevance_score=relevance_score,
                        match_reasons=match_reasons
                    )
                    
                    role_matches.append(role_match)
                    
                except Exception as e:
                    logger.warning(f"Failed to process search result: {str(e)}")
                    continue
            
            # Sort by relevance score (highest first)
            role_matches.sort(key=lambda x: x.relevance_score, reverse=True)
            
            logger.info(f"Found {len(role_matches)} roles above {self.MIN_RELEVANCY_SCORE:.0%} relevancy threshold")
            
            return role_matches
            
        except (AzureOpenAIError, AzureSearchError):
            raise
        except Exception as e:
            logger.error(f"Role matching failed: {str(e)}")
            raise BusinessLogicError(f"Failed to find matching roles: {str(e)}")
    
    def create_custom_role(
        self,
        job_description: JobDescription,
        industry_id: str,
        created_by_user_id: str
    ) -> Role:
        """
        Create a new custom role from job description.
        
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
                rewritten_description = self.openai_service.rewrite_job_description(
                    job_description.title,
                    job_description.description
                )
            except Exception as e:
                logger.warning(f"Failed to rewrite job description, using original: {str(e)}")
                rewritten_description = job_description.description
            
            # Generate keywords using AI
            try:
                generated_keywords = self.openai_service.generate_role_keywords(
                    job_description.title,
                    job_description.description
                )
            except Exception as e:
                logger.warning(f"Failed to generate keywords, using fallback: {str(e)}")
                from core.utils import generate_search_keywords
                generated_keywords = generate_search_keywords(
                    f"{job_description.title} {job_description.description}"
                )
            
            # Create role in Supabase
            role_creation_result = self.supabase_service.create_new_role(
                title=job_description.title,
                description=rewritten_description,
                industry_id=industry_id,
                search_keywords=generated_keywords,
                hierarchy_level=job_description.hierarchy_level.value
            )
            
            if not role_creation_result.get('success'):
                raise BusinessLogicError(
                    role_creation_result.get('error', 'Failed to create role in database')
                )
            
            new_role_id = role_creation_result['role_id']
            
            # Get the complete role data with industry information
            role_with_industry = self.supabase_service.get_role_with_industry(new_role_id)
            if not role_with_industry:
                raise BusinessLogicError("Failed to retrieve created role")
            
            # Create Role instance
            role = Role.from_supabase_data(role_with_industry)
            
            # Add role to Azure Search index (non-blocking)
            try:
                search_index_result = self.azure_search_service.add_single_role_to_index(role_with_industry)
                if not search_index_result.get('success'):
                    logger.warning(f"Failed to add role to search index: {search_index_result.get('error')}")
            except Exception as e:
                logger.warning(f"Failed to add role to search index: {str(e)}")
            
            return role
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Failed to create custom role: {str(e)}")
            raise BusinessLogicError(f"Failed to create custom role: {str(e)}")
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """
        Get role by ID.
        
        Args:
            role_id: Role identifier
            
        Returns:
            Role instance or None if not found
        """
        try:
            role_data = self.supabase_service.get_role_with_industry(role_id)
            if not role_data:
                return None
            
            return Role.from_supabase_data(role_data)
            
        except Exception as e:
            logger.error(f"Failed to get role {role_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve role: {str(e)}")
    
    def get_all_roles_for_industry(self, industry_id: str) -> List[Role]:
        """
        Get all active roles for a specific industry.
        
        Args:
            industry_id: Industry identifier
            
        Returns:
            List of Role instances
        """
        try:
            roles_data = self.supabase_service.get_all_roles_with_industry()
            
            # Filter by industry and active status
            industry_roles = []
            for role_data in roles_data:
                if (role_data.get('industry_id') == industry_id and 
                    role_data.get('is_active', True)):
                    
                    role = Role.from_supabase_data(role_data)
                    industry_roles.append(role)
            
            # Sort by title
            industry_roles.sort(key=lambda x: x.title)
            
            return industry_roles
            
        except Exception as e:
            logger.error(f"Failed to get roles for industry {industry_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve industry roles: {str(e)}")
    
    def get_industry_by_id(self, industry_id: str) -> Optional[Industry]:
        """
        Get industry by ID.
        
        Args:
            industry_id: Industry identifier
            
        Returns:
            Industry instance or None if not found
        """
        try:
            # Get industries from service
            industries_data = self.supabase_service.get_available_industries()
            
            for industry_data in industries_data:
                if industry_data.get('id') == industry_id:
                    return Industry.from_supabase_data(industry_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get industry {industry_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve industry: {str(e)}")
    
    def get_all_industries(self) -> List[Industry]:
        """
        Get all available industries.
        
        Returns:
            List of Industry instances
        """
        try:
            industries_data = self.supabase_service.get_available_industries()
            
            industries = []
            for industry_data in industries_data:
                industry = Industry.from_supabase_data(industry_data)
                industries.append(industry)
            
            return industries
            
        except Exception as e:
            logger.error(f"Failed to get industries: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve industries: {str(e)}")
    
    def record_role_selection(
        self,
        user_id: str,
        role_id: str,
        role_source: RoleSource,
        role_details: Optional[Dict[str, Any]] = None
    ) -> UserRoleSelection:
        """
        Record a user's role selection.
        
        Args:
            user_id: User identifier
            role_id: Selected role identifier
            role_source: How the role was obtained
            role_details: Additional role selection details
            
        Returns:
            UserRoleSelection instance
        """
        try:
            # Record in user session for tracking
            result = self.supabase_service.update_user_session_role_source(
                auth0_id=user_id,  # Note: This expects auth0_id, may need adjustment
                role_source=role_source.value,
                role_details=role_details or {}
            )
            
            if not result.get('success'):
                logger.warning(f"Failed to record role selection in session: {result.get('error')}")
            
            return UserRoleSelection(
                user_id=user_id,
                role_id=role_id,
                role_source=role_source,
                selected_at=datetime.utcnow(),
                role_details=role_details
            )
            
        except Exception as e:
            logger.error(f"Failed to record role selection: {str(e)}")
            raise BusinessLogicError(f"Failed to record role selection: {str(e)}")
    
    def search_roles(
        self,
        query: str,
        industry_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[RoleMatch]:
        """
        Search for roles using text query.
        
        Args:
            query: Search text query
            industry_filter: Optional industry filter
            limit: Maximum number of results to return
            
        Returns:
            List of RoleMatch instances sorted by relevance
        """
        try:
            # Create a simple job description for search
            job_description = JobDescription(
                title=query,
                description=query,
                industry=industry_filter
            )
            
            # Use existing find_matching_roles method
            return self.find_matching_roles(
                job_description=job_description,
                industry_filter=industry_filter,
                max_results=limit
            )
            
        except Exception as e:
            logger.error(f"Role search failed: {str(e)}")
            raise BusinessLogicError(f"Failed to search roles: {str(e)}")
    
    def track_role_selection(
        self,
        auth0_id: str,
        role_id: str,
        source: str,
        original_description: Optional[str] = None
    ) -> None:
        """
        Track a user's role selection.
        
        Args:
            auth0_id: User's Auth0 ID
            role_id: Selected role ID
            source: Role source ('selected' or 'created')
            original_description: Original job description if role was created
        """
        try:
            # Use existing record_role_selection method
            role_source = RoleSource.SELECTED if source == 'selected' else RoleSource.CREATED
            role_details = {}
            if original_description:
                role_details['original_description'] = original_description
            
            self.record_role_selection(
                user_id=auth0_id,
                role_id=role_id,
                role_source=role_source,
                role_details=role_details
            )
            
        except Exception as e:
            logger.warning(f"Failed to track role selection: {str(e)}")
    
    def create_new_role(
        self,
        title: str,
        description: str,
        industry_id: str,
        hierarchy_level: str,
        created_by_user_id: str
    ) -> Role:
        """
        Create a new role (wrapper for create_custom_role).
        
        Args:
            title: Role title
            description: Role description
            industry_id: Industry ID
            hierarchy_level: Hierarchy level
            created_by_user_id: User ID who created the role
            
        Returns:
            Created Role instance
        """
        try:
            # Convert hierarchy level to enum
            hierarchy_enum = HierarchyLevel.ASSOCIATE
            try:
                hierarchy_enum = HierarchyLevel(hierarchy_level)
            except ValueError:
                pass  # Keep default if invalid
            
            # Create job description object
            job_description = JobDescription(
                title=title,
                description=description,
                hierarchy_level=hierarchy_enum
            )
            
            # Use existing create_custom_role method
            return self.create_custom_role(
                job_description=job_description,
                industry_id=industry_id,
                created_by_user_id=created_by_user_id
            )
            
        except Exception as e:
            logger.error(f"Failed to create new role: {str(e)}")
            raise BusinessLogicError(f"Failed to create new role: {str(e)}")
    
    def get_role_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about roles and usage.
        
        Returns:
            Dictionary with role statistics
        """
        try:
            roles_data = self.supabase_service.get_all_roles_with_industry()
            
            # Calculate statistics
            total_roles = len(roles_data)
            active_roles = len([r for r in roles_data if r.get('is_active', True)])
            
            # Group by industry
            industry_counts = {}
            hierarchy_counts = {}
            
            for role_data in roles_data:
                if role_data.get('is_active', True):
                    industry = role_data.get('industry_name', 'Unknown')
                    hierarchy = role_data.get('hierarchy_level', 'associate')
                    
                    industry_counts[industry] = industry_counts.get(industry, 0) + 1
                    hierarchy_counts[hierarchy] = hierarchy_counts.get(hierarchy, 0) + 1
            
            return {
                'total_roles': total_roles,
                'active_roles': active_roles,
                'inactive_roles': total_roles - active_roles,
                'roles_by_industry': industry_counts,
                'roles_by_hierarchy': hierarchy_counts,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get role statistics: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve role statistics: {str(e)}")