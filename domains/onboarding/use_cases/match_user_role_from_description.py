"""
Role matching from job description use case.

Handles AI-powered role matching based on user's job description.
"""

from typing import List, Optional
import logging

from core.exceptions import (
    AzureOpenAIError,
    AzureSearchError,
    BusinessLogicError
)
from authentication.models.role import JobDescription, RoleMatch
from infrastructure.external_services.azure.client import IAzureCognitiveSearchClient
from infrastructure.external_services.openai.client import IOpenAIClient

logger = logging.getLogger(__name__)


class MatchUserRoleFromDescription:
    """
    Use case for matching roles based on job description.
    
    Uses AI services to find existing roles that match
    the user's job description and requirements.
    """
    
    # Configuration constants
    MIN_RELEVANCY_SCORE = 0.7  # 70% minimum relevancy score
    
    def __init__(
        self,
        search_client: IAzureCognitiveSearchClient,
        ai_client: IOpenAIClient
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            search_client: Azure Search client for role matching
            ai_client: OpenAI client for embedding generation
        """
        self.search_client = search_client
        self.ai_client = ai_client
    
    def execute(
        self,
        job_description: JobDescription,
        industry_filter: Optional[str] = None,
        max_results: int = 5
    ) -> List[RoleMatch]:
        """
        Execute role matching from job description.
        
        Args:
            job_description: Job description to match against
            industry_filter: Optional industry filter
            max_results: Maximum number of results to return
            
        Returns:
            List of RoleMatch instances sorted by relevance
            
        Raises:
            AzureOpenAIError: If embedding generation fails
            AzureSearchError: If search fails
            BusinessLogicError: If role matching fails
        """
        try:
            # Generate embedding for job description
            try:
                query_embedding = self.ai_client.create_embedding(job_description.search_text)
            except Exception as e:
                logger.error(f"Failed to generate embedding for job search: {str(e)}")
                raise AzureOpenAIError(f"Failed to generate search embedding: {str(e)}")
            
            # Prepare search filters
            filters = None
            if industry_filter:
                filters = f"industry_name eq '{industry_filter}'"
            
            # Perform hybrid search
            try:
                search_result = self.search_client.hybrid_search(
                    index_name="roles",
                    search_text=f"{job_description.title} {job_description.description}",
                    vector=query_embedding,
                    top_k=max_results,
                    filter_expression=filters
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
                    from authentication.models.role import Role
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
                    
                    # Create match reasons based on search results
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