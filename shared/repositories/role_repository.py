"""
Role repository implementation using Supabase and Azure Search.
Handles role-related data access operations with vector search capabilities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from core.interfaces import RoleRepositoryInterface
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)
from authentication.models.role import Role, RoleMatch, JobDescription, HierarchyLevel
from authentication.services.supabase_service import SupabaseService
from authentication.services.azure_search_service import AzureSearchService

logger = logging.getLogger(__name__)


class RoleRepository(RoleRepositoryInterface):
    """
    Concrete implementation of RoleRepositoryInterface.
    Uses Supabase for data storage and Azure Search for vector similarity.
    """
    
    def __init__(
        self, 
        supabase_service: Optional[SupabaseService] = None,
        search_service: Optional[AzureSearchService] = None
    ):
        self.supabase = supabase_service or SupabaseService()
        self.search_service = search_service or AzureSearchService()
    
    def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        try:
            response = self.supabase.client.table('roles')\
                .select('*, industries(id, name)')\
                .eq('id', role_id)\
                .execute()
            
            if not response.data:
                return None
            
            return Role.from_supabase_data(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get role by ID {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve role: {str(e)}")
    
    def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        """Search roles by embedding similarity."""
        try:
            # Use Azure Search for vector similarity
            search_results = self.search_service.search_roles_by_embedding(
                embedding=embedding,
                top=limit
            )
            
            role_matches = []
            for result in search_results:
                # Get full role data from Supabase
                role_response = self.supabase.client.table('roles')\
                    .select('*, industries(id, name)')\
                    .eq('id', result['id'])\
                    .execute()
                
                if role_response.data:
                    role = Role.from_supabase_data(role_response.data[0])
                    role_match = RoleMatch(
                        role=role,
                        relevance_score=result.get('@search.score', 0.0),
                        match_reason=result.get('match_reason', ''),
                        embedding_similarity=result.get('embedding_similarity', 0.0)
                    )
                    role_matches.append(role_match)
            
            return role_matches
            
        except Exception as e:
            logger.error(f"Failed to search roles by embedding: {str(e)}")
            raise DatabaseError(f"Role search failed: {str(e)}")
    
    def create(self, role_data: Dict[str, Any]) -> Role:
        """Create a new role."""
        try:
            # Validate required fields
            required_fields = ['title', 'description', 'industry_id']
            for field in required_fields:
                if field not in role_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Set default values
            role_data.setdefault('hierarchy_level', HierarchyLevel.ASSOCIATE.value)
            role_data.setdefault('is_active', True)
            role_data.setdefault('created_at', datetime.utcnow().isoformat())
            role_data.setdefault('updated_at', datetime.utcnow().isoformat())
            
            # Insert into Supabase
            response = self.supabase.client.table('roles')\
                .insert(role_data)\
                .execute()
            
            if not response.data:
                raise DatabaseError("Role creation failed - no data returned")
            
            created_role = Role.from_supabase_data(response.data[0])
            
            # Index in Azure Search if embedding is provided
            if 'embedding' in role_data:
                try:
                    self.search_service.upload_role({
                        'id': created_role.id,
                        'title': created_role.title,
                        'description': created_role.description,
                        'hierarchy_level': created_role.hierarchy_level.value,
                        'industry_id': role_data['industry_id'],
                        'embedding': role_data['embedding'],
                        'search_keywords': role_data.get('search_keywords', [])
                    })
                except Exception as search_error:
                    logger.warning(f"Failed to index role in search: {str(search_error)}")
            
            return created_role
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            raise DatabaseError(f"Role creation failed: {str(e)}")
    
    def update(self, role_id: str, data: Dict[str, Any]) -> Role:
        """Update role data."""
        try:
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.supabase.client.table('roles')\
                .update(data)\
                .eq('id', role_id)\
                .execute()
            
            if not response.data:
                raise ResourceNotFoundError("Role", role_id)
            
            updated_role = Role.from_supabase_data(response.data[0])
            
            # Update search index if role data changed
            try:
                search_data = {
                    'id': updated_role.id,
                    'title': updated_role.title,
                    'description': updated_role.description,
                    'hierarchy_level': updated_role.hierarchy_level.value,
                }
                
                # Add embedding if provided
                if 'embedding' in data:
                    search_data['embedding'] = data['embedding']
                
                self.search_service.update_role(search_data)
            except Exception as search_error:
                logger.warning(f"Failed to update role in search index: {str(search_error)}")
            
            return updated_role
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update role {role_id}: {str(e)}")
            raise DatabaseError(f"Role update failed: {str(e)}")
    
    def get_by_industry(self, industry_id: str) -> List[Role]:
        """Get roles by industry."""
        try:
            response = self.supabase.client.table('roles')\
                .select('*, industries(id, name)')\
                .eq('industry_id', industry_id)\
                .eq('is_active', True)\
                .order('title')\
                .execute()
            
            return [Role.from_supabase_data(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get roles by industry {industry_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve roles by industry: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics."""
        try:
            # Total roles
            total_response = self.supabase.client.table('roles')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Custom vs predefined roles
            custom_response = self.supabase.client.table('roles')\
                .select('id', count='exact')\
                .eq('is_custom', True)\
                .eq('is_active', True)\
                .execute()
            
            # Role selections (users who have selected roles)
            selections_response = self.supabase.client.table('users')\
                .select('selected_role_id', count='exact')\
                .not_('selected_role_id', 'is', None)\
                .execute()
            
            # Most popular roles
            popular_roles_response = self.supabase.client.table('users')\
                .select('selected_role_id, roles(title)', count='exact')\
                .not_('selected_role_id', 'is', None)\
                .execute()
            
            # Group by role ID
            role_popularity = {}
            for user in popular_roles_response.data:
                role_id = user['selected_role_id']
                if role_id in role_popularity:
                    role_popularity[role_id]['count'] += 1
                else:
                    role_popularity[role_id] = {
                        'count': 1,
                        'title': user.get('roles', {}).get('title', 'Unknown')
                    }
            
            # Sort by popularity
            most_popular = sorted(
                role_popularity.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )[:5]
            
            return {
                'total_roles': total_response.count,
                'custom_roles': custom_response.count,
                'predefined_roles': total_response.count - custom_response.count,
                'roles_selected': selections_response.count,
                'selection_rate': (
                    selections_response.count / max(total_response.count, 1) * 100
                ),
                'most_popular_roles': [
                    {
                        'role_id': role_id,
                        'title': data['title'],
                        'selection_count': data['count']
                    }
                    for role_id, data in most_popular
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get role statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve role statistics: {str(e)}")
    
    def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Role]:
        """Search roles by text query."""
        try:
            # Build query
            query_builder = self.supabase.client.table('roles')\
                .select('*, industries(id, name)')\
                .eq('is_active', True)
            
            # Add industry filter if provided
            if industry_id:
                query_builder = query_builder.eq('industry_id', industry_id)
            
            # Text search using ilike
            query_builder = query_builder.or_(
                f'title.ilike.%{query}%,description.ilike.%{query}%'
            )
            
            response = query_builder.limit(limit).execute()
            
            return [Role.from_supabase_data(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to search roles by text '{query}': {str(e)}")
            raise DatabaseError(f"Text search failed: {str(e)}")
    
    def get_roles_needing_embedding(self, limit: int = 100) -> List[Role]:
        """Get roles that don't have embeddings yet."""
        try:
            response = self.supabase.client.table('roles')\
                .select('*, industries(id, name)')\
                .is_('embedding', None)\
                .eq('is_active', True)\
                .limit(limit)\
                .execute()
            
            return [Role.from_supabase_data(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get roles needing embedding: {str(e)}")
            raise DatabaseError(f"Failed to retrieve roles needing embedding: {str(e)}")
    
    def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        """Update role embedding."""
        try:
            response = self.supabase.client.table('roles')\
                .update({'embedding': embedding, 'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', role_id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update embedding for role {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to update role embedding: {str(e)}")