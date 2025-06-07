"""
Industry repository implementation using Supabase.
Concrete implementation of IIndustryRepository for data persistence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from domains.onboarding.repositories.interfaces import IIndustryRepository
from domains.authentication.models.role import Industry
from domains.shared.repositories.base_repository import BaseRepository
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class IndustryRepositoryImpl(BaseRepository[Dict[str, Any], str], IIndustryRepository):
    """
    Concrete implementation of IIndustryRepository using Supabase.
    Works with industry data as dictionaries per interface specification.
    """
    
    def __init__(self, supabase_client):
        super().__init__('industries')
        self.client = supabase_client
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find industry by ID."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('id', id)\
                .eq('is_active', True)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_dict(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get industry by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry: {str(e)}")
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find all industries matching filters."""
        try:
            query = self.client.table(self.table_name)\
                .select('*')\
                .eq('is_active', True)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = await query.order('sort_order').execute()
            return [self._to_dict(industry_data) for industry_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get industries with filters {filters}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industries: {str(e)}")
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Save entity (create or update)."""
        try:
            if entity.get('id'):
                # Update existing industry
                entity['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .update(entity)\
                    .eq('id', entity['id'])\
                    .execute()
                
                if not response.data:
                    raise ResourceNotFoundError("Industry", entity['id'])
                
                return self._to_dict(response.data[0])
            else:
                # Create new industry
                entity['created_at'] = datetime.utcnow().isoformat()
                entity['updated_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .insert(entity)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("Industry creation failed - no data returned")
                
                return self._to_dict(response.data[0])
                
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to save industry: {str(e)}")
            raise DatabaseError(f"Industry save failed: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete industry by ID (soft delete)."""
        try:
            response = await self.client.table(self.table_name)\
                .update({'is_active': False, 'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete industry {id}: {str(e)}")
            raise DatabaseError(f"Industry deletion failed: {str(e)}")
    
    async def get_by_name(self, industry_name: str) -> Optional[Dict[str, Any]]:
        """Get industry by name."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('name', industry_name)\
                .eq('is_active', True)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_dict(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get industry by name {industry_name}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry: {str(e)}")
    
    async def get_with_role_counts(self) -> List[Dict[str, Any]]:
        """Get industries with role counts."""
        try:
            # Get industries with role counts using a join
            response = await self.client.table(self.table_name)\
                .select('*, roles(count)')\
                .eq('is_active', True)\
                .order('sort_order')\
                .execute()
            
            result = []
            for industry_data in response.data:
                industry = self._to_dict(industry_data)
                
                # Count roles for this industry
                role_count_response = await self.client.table('roles')\
                    .select('id', count='exact')\
                    .eq('industry_id', industry['id'])\
                    .eq('is_active', True)\
                    .execute()
                
                industry['role_count'] = role_count_response.count
                result.append(industry)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get industries with role counts: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industries with role counts: {str(e)}")
    
    async def get_popular_industries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular industries based on user selections."""
        try:
            # Get industry selections from users
            selections_response = await self.client.table('users')\
                .select('industry_id')\
                .not_('industry_id', 'is', None)\
                .execute()
            
            # Count selections per industry
            industry_counts = {}
            for selection in selections_response.data:
                industry_id = selection['industry_id']
                industry_counts[industry_id] = industry_counts.get(industry_id, 0) + 1
            
            # Get industry details for the most popular ones
            popular_industry_ids = sorted(
                industry_counts.keys(),
                key=lambda x: industry_counts[x],
                reverse=True
            )[:limit]
            
            if not popular_industry_ids:
                return []
            
            response = await self.client.table(self.table_name)\
                .select('*')\
                .in_('id', popular_industry_ids)\
                .eq('is_active', True)\
                .execute()
            
            # Add selection count to each industry
            result = []
            for industry_data in response.data:
                industry = self._to_dict(industry_data)
                industry['selection_count'] = industry_counts.get(industry['id'], 0)
                result.append(industry)
            
            # Sort by selection count
            result.sort(key=lambda x: x['selection_count'], reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get popular industries: {str(e)}")
            raise DatabaseError(f"Failed to retrieve popular industries: {str(e)}")
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search industries by name or description."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .or_(f'name.ilike.%{query}%,description.ilike.%{query}%')\
                .eq('is_active', True)\
                .limit(limit)\
                .execute()
            
            return [self._to_dict(industry_data) for industry_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to search industries with query '{query}': {str(e)}")
            raise DatabaseError(f"Industry search failed: {str(e)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get industry statistics."""
        try:
            # Total industries
            total_response = await self.client.table(self.table_name)\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Total users with industry selections
            users_with_industry_response = await self.client.table('users')\
                .select('id', count='exact')\
                .not_('industry_id', 'is', None)\
                .execute()
            
            # Total users
            total_users_response = await self.client.table('users')\
                .select('id', count='exact')\
                .execute()
            
            # Industries with roles
            industries_with_roles_response = await self.client.table('roles')\
                .select('industry_id')\
                .eq('is_active', True)\
                .execute()
            
            unique_industries_with_roles = len(set(
                role['industry_id'] for role in industries_with_roles_response.data
            ))
            
            # Total roles
            total_roles_response = await self.client.table('roles')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            selection_rate = 0
            if total_users_response.count > 0:
                selection_rate = (users_with_industry_response.count / total_users_response.count) * 100
            
            return {
                'total_industries': total_response.count,
                'industries_with_roles': unique_industries_with_roles,
                'industries_without_roles': total_response.count - unique_industries_with_roles,
                'total_users_with_industry': users_with_industry_response.count,
                'total_users': total_users_response.count,
                'industry_selection_rate': round(selection_rate, 2),
                'total_roles': total_roles_response.count,
                'avg_roles_per_industry': round(
                    total_roles_response.count / max(unique_industries_with_roles, 1), 2
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get industry statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry statistics: {str(e)}")
    
    def _to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database row to dictionary (interface requirement)."""
        # Clean and format the data
        result = {
            'id': data.get('id'),
            'name': data.get('name'),
            'description': data.get('description'),
            'sort_order': data.get('sort_order', 0),
            'is_active': data.get('is_active', True),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at')
        }
        
        # Add any additional fields that might be present
        for key, value in data.items():
            if key not in result:
                result[key] = value
        
        return result