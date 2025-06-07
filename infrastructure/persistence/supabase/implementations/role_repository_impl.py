"""
Role repository implementation using Supabase and Azure Search.
Concrete implementation of IRoleRepository for data persistence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from domains.authentication.repositories.interfaces import IRoleRepository
from domains.authentication.models.role import Role, RoleMatch, HierarchyLevel
from domains.shared.repositories.base_repository import BaseRepository
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class RoleRepositoryImpl(BaseRepository[Role, str], IRoleRepository):
    """
    Concrete implementation of IRoleRepository.
    Uses Supabase for data storage and search service for vector similarity.
    """
    
    def __init__(self, supabase_client, search_service=None):
        super().__init__('roles')
        self.client = supabase_client
        self.search_service = search_service
    
    async def find_by_id(self, id: str) -> Optional[Role]:
        """Find role by ID."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .eq('id', id)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get role by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve role: {str(e)}")
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Role]:
        """Find all roles matching filters."""
        try:
            query = self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .eq('is_active', True)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = await query.order('title').execute()
            return [self._to_entity(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get roles with filters {filters}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve roles: {str(e)}")
    
    async def save(self, entity: Role) -> Role:
        """Save entity (create or update)."""
        try:
            data = self._to_dict(entity)
            
            if entity.id:
                # Update existing role
                data['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .update(data)\
                    .eq('id', entity.id)\
                    .execute()
                
                if not response.data:
                    raise ResourceNotFoundError("Role", entity.id)
                
                updated_role = self._to_entity(response.data[0])
                
                # Update search index if search service is available
                if self.search_service:
                    try:
                        await self._update_search_index(updated_role)
                    except Exception as search_error:
                        logger.warning(f"Failed to update role in search index: {str(search_error)}")
                
                return updated_role
            else:
                # Create new role
                data['created_at'] = datetime.utcnow().isoformat()
                data['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .insert(data)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("Role creation failed - no data returned")
                
                created_role = self._to_entity(response.data[0])
                
                # Index in search service if available
                if self.search_service:
                    try:
                        await self._index_role(created_role)
                    except Exception as search_error:
                        logger.warning(f"Failed to index role in search: {str(search_error)}")
                
                return created_role
                
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to save role: {str(e)}")
            raise DatabaseError(f"Role save failed: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete role by ID (soft delete by marking inactive)."""
        try:
            # Soft delete by marking as inactive
            data = {
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = await self.client.table(self.table_name)\
                .update(data)\
                .eq('id', id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete role {id}: {str(e)}")
            raise DatabaseError(f"Role deletion failed: {str(e)}")
    
    async def find_by_name(self, name: str) -> Optional[Role]:
        """Find role by name."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .eq('title', name)\
                .eq('is_active', True)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get role by name {name}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve role: {str(e)}")
    
    async def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        """Search roles by embedding similarity."""
        try:
            if not self.search_service:
                logger.warning("Search service not available, returning empty results")
                return []
            
            # Use search service for vector similarity
            search_results = await self.search_service.search_roles_by_embedding(
                embedding=embedding,
                top=limit
            )
            
            role_matches = []
            for result in search_results:
                # Get full role data from Supabase
                role_response = await self.client.table(self.table_name)\
                    .select('*, industries(id, name)')\
                    .eq('id', result['id'])\
                    .execute()
                
                if role_response.data:
                    role = self._to_entity(role_response.data[0])
                    role_match = RoleMatch(
                        role=role,
                        relevance_score=result.get('@search.score', 0.0),
                        match_reasons=[result.get('match_reason', '')]
                    )
                    role_matches.append(role_match)
            
            return role_matches
            
        except Exception as e:
            logger.error(f"Failed to search roles by embedding: {str(e)}")
            raise DatabaseError(f"Role search failed: {str(e)}")
    
    async def get_by_industry(self, industry_id: str) -> List[Role]:
        """Get roles by industry."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .eq('industry_id', industry_id)\
                .eq('is_active', True)\
                .order('title')\
                .execute()
            
            return [self._to_entity(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get roles by industry {industry_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve roles by industry: {str(e)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics."""
        try:
            # Total roles
            total_response = await self.client.table(self.table_name)\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Roles by hierarchy level
            hierarchy_counts = {}
            for level in HierarchyLevel:
                level_response = await self.client.table(self.table_name)\
                    .select('id', count='exact')\
                    .eq('hierarchy_level', level.value)\
                    .eq('is_active', True)\
                    .execute()
                hierarchy_counts[level.value] = level_response.count
            
            # Role selections (from users table)
            selections_response = await self.client.table('users')\
                .select('selected_role_id', count='exact')\
                .not_('selected_role_id', 'is', None)\
                .execute()
            
            return {
                'total_roles': total_response.count,
                'by_hierarchy': hierarchy_counts,
                'total_selections': selections_response.count,
                'selection_rate': (
                    selections_response.count / max(total_response.count, 1) * 100
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get role statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve role statistics: {str(e)}")
    
    async def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Role]:
        """Search roles by text query."""
        try:
            # Build query
            query_builder = self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .eq('is_active', True)
            
            # Add industry filter if provided
            if industry_id:
                query_builder = query_builder.eq('industry_id', industry_id)
            
            # Text search using ilike
            query_builder = query_builder.or_(
                f'title.ilike.%{query}%,description.ilike.%{query}%'
            )
            
            response = await query_builder.limit(limit).execute()
            
            return [self._to_entity(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to search roles by text '{query}': {str(e)}")
            raise DatabaseError(f"Text search failed: {str(e)}")
    
    async def get_roles_needing_embedding(self, limit: int = 100) -> List[Role]:
        """Get roles that don't have embeddings yet."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*, industries(id, name)')\
                .is_('embedding', None)\
                .eq('is_active', True)\
                .limit(limit)\
                .execute()
            
            return [self._to_entity(role_data) for role_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get roles needing embedding: {str(e)}")
            raise DatabaseError(f"Failed to retrieve roles needing embedding: {str(e)}")
    
    async def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        """Update role embedding."""
        try:
            response = await self.client.table(self.table_name)\
                .update({\
                    'embedding': embedding, \
                    'updated_at': datetime.utcnow().isoformat()\
                })\
                .eq('id', role_id)\
                .execute()
            
            success = len(response.data) > 0
            
            # Update search index if successful and search service available
            if success and self.search_service:
                try:
                    role = await self.find_by_id(role_id)
                    if role:
                        await self._update_search_index(role, embedding)
                except Exception as search_error:
                    logger.warning(f"Failed to update search index after embedding update: {str(search_error)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update embedding for role {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to update role embedding: {str(e)}")
    
    def _to_entity(self, data: Dict[str, Any]) -> Role:
        """Convert database row to Role entity."""
        # Extract industry name from joined data
        if 'industries' in data and data['industries']:
            data['industry_name'] = data['industries']['name']
        
        return Role.from_supabase_data(data)
    
    def _to_dict(self, entity: Role) -> Dict[str, Any]:
        """Convert Role entity to database row."""
        return {
            'title': entity.title,
            'description': entity.description,
            'industry_id': entity.industry_id,
            'hierarchy_level': entity.hierarchy_level.value,
            'search_keywords': entity.search_keywords,
            'is_active': entity.is_active,
        }
    
    async def _index_role(self, role: Role, embedding: Optional[List[float]] = None) -> None:
        """Index role in search service."""
        if not self.search_service:
            return
        
        search_data = {
            'id': role.id,
            'title': role.title,
            'description': role.description,
            'hierarchy_level': role.hierarchy_level.value,
            'industry_id': role.industry_id,
            'search_keywords': role.search_keywords or [],
        }
        
        if embedding:
            search_data['embedding'] = embedding
        
        await self.search_service.upload_role(search_data)
    
    async def _update_search_index(self, role: Role, embedding: Optional[List[float]] = None) -> None:
        """Update role in search index."""
        if not self.search_service:
            return
        
        search_data = {
            'id': role.id,
            'title': role.title,
            'description': role.description,
            'hierarchy_level': role.hierarchy_level.value,
            'industry_id': role.industry_id,
            'search_keywords': role.search_keywords or [],
        }
        
        if embedding:
            search_data['embedding'] = embedding
        
        await self.search_service.update_role(search_data)