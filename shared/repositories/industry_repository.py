"""
Industry repository implementation using Supabase.
Handles industry-related data access operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from core.interfaces import IndustryRepositoryInterface
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class IndustryRepository(IndustryRepositoryInterface):
    """
    Concrete implementation of IndustryRepositoryInterface using Supabase.
    Provides CRUD operations for industries.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase = supabase_service or SupabaseService()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active industries."""
        try:
            response = self.supabase.client.table('industries')\
                .select('*')\
                .eq('status', 'available')\
                .order('sort_order, name')\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get all industries: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industries: {str(e)}")
    
    def get_by_id(self, industry_id: str) -> Optional[Dict[str, Any]]:
        """Get industry by ID."""
        try:
            response = self.supabase.client.table('industries')\
                .select('*')\
                .eq('id', industry_id)\
                .execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get industry by ID {industry_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry: {str(e)}")
    
    def get_by_name(self, industry_name: str) -> Optional[Dict[str, Any]]:
        """Get industry by name."""
        try:
            response = self.supabase.client.table('industries')\
                .select('*')\
                .eq('name', industry_name)\
                .eq('status', 'available')\
                .execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get industry by name {industry_name}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry: {str(e)}")
    
    def create(self, industry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new industry."""
        try:
            # Validate required fields
            required_fields = ['name']
            for field in required_fields:
                if field not in industry_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Set default values
            industry_data.setdefault('is_active', True)
            industry_data.setdefault('sort_order', 999)  # Put at end by default
            industry_data.setdefault('created_at', datetime.utcnow().isoformat())
            industry_data.setdefault('updated_at', datetime.utcnow().isoformat())
            
            response = self.supabase.client.table('industries')\
                .insert(industry_data)\
                .execute()
            
            if not response.data:
                raise DatabaseError("Industry creation failed - no data returned")
            
            return response.data[0]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create industry: {str(e)}")
            raise DatabaseError(f"Industry creation failed: {str(e)}")
    
    def update(self, industry_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update industry data."""
        try:
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.supabase.client.table('industries')\
                .update(data)\
                .eq('id', industry_id)\
                .execute()
            
            if not response.data:
                raise ResourceNotFoundError("Industry", industry_id)
            
            return response.data[0]
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update industry {industry_id}: {str(e)}")
            raise DatabaseError(f"Industry update failed: {str(e)}")
    
    def delete(self, industry_id: str) -> bool:
        """Soft delete industry by marking as inactive."""
        try:
            response = self.supabase.client.table('industries')\
                .update({
                    'is_active': False,
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('id', industry_id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete industry {industry_id}: {str(e)}")
            raise DatabaseError(f"Industry deletion failed: {str(e)}")
    
    def get_with_role_counts(self) -> List[Dict[str, Any]]:
        """Get industries with role counts."""
        try:
            # Get industries with role counts using a join
            response = self.supabase.client.table('industries')\
                .select('*, roles(count)')\
                .eq('is_active', True)\
                .order('sort_order, name')\
                .execute()
            
            # Process the data to include role counts
            industries_with_counts = []
            for industry in response.data:
                industry_data = dict(industry)
                
                # Count active roles for this industry
                roles_response = self.supabase.client.table('roles')\
                    .select('id', count='exact')\
                    .eq('industry_id', industry['id'])\
                    .eq('is_active', True)\
                    .execute()
                
                industry_data['role_count'] = roles_response.count
                industries_with_counts.append(industry_data)
            
            return industries_with_counts
            
        except Exception as e:
            logger.error(f"Failed to get industries with role counts: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industries with counts: {str(e)}")
    
    def get_popular_industries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular industries based on user selections."""
        try:
            # Get industry usage from user selections
            usage_response = self.supabase.client.table('users')\
                .select('industry_id, industries(name)')\
                .not_('industry_id', 'is', None)\
                .execute()
            
            # Count selections per industry
            industry_counts = {}
            for user in usage_response.data:
                industry_id = user['industry_id']
                if industry_id in industry_counts:
                    industry_counts[industry_id]['count'] += 1
                else:
                    industry_counts[industry_id] = {
                        'count': 1,
                        'name': user.get('industries', {}).get('name', 'Unknown')
                    }
            
            # Sort by popularity and get full industry data
            popular_industry_ids = sorted(
                industry_counts.keys(),
                key=lambda x: industry_counts[x]['count'],
                reverse=True
            )[:limit]
            
            if not popular_industry_ids:
                return []
            
            # Get full industry data for popular industries
            response = self.supabase.client.table('industries')\
                .select('*')\
                .in_('id', popular_industry_ids)\
                .execute()
            
            # Add usage counts to the results
            popular_industries = []
            for industry in response.data:
                industry_data = dict(industry)
                industry_data['user_count'] = industry_counts[industry['id']]['count']
                popular_industries.append(industry_data)
            
            # Sort by user count
            popular_industries.sort(key=lambda x: x['user_count'], reverse=True)
            
            return popular_industries
            
        except Exception as e:
            logger.error(f"Failed to get popular industries: {str(e)}")
            raise DatabaseError(f"Failed to retrieve popular industries: {str(e)}")
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search industries by name or description."""
        try:
            response = self.supabase.client.table('industries')\
                .select('*')\
                .eq('is_active', True)\
                .or_(f'name.ilike.%{query}%,description.ilike.%{query}%')\
                .limit(limit)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to search industries with query '{query}': {str(e)}")
            raise DatabaseError(f"Industry search failed: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get industry statistics."""
        try:
            # Total industries
            total_response = self.supabase.client.table('industries')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Industries with roles
            industries_with_roles = self.supabase.client.table('roles')\
                .select('industry_id')\
                .eq('is_active', True)\
                .execute()
            
            unique_industries_with_roles = len(set(
                role['industry_id'] for role in industries_with_roles.data
            ))
            
            # User selections
            user_selections = self.supabase.client.table('users')\
                .select('industry_id', count='exact')\
                .not_('industry_id', 'is', None)\
                .execute()
            
            return {
                'total_industries': total_response.count,
                'industries_with_roles': unique_industries_with_roles,
                'user_selections': user_selections.count,
                'coverage_rate': (
                    unique_industries_with_roles / max(total_response.count, 1) * 100
                ),
                'selection_rate': (
                    user_selections.count / max(total_response.count, 1) * 100
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get industry statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve industry statistics: {str(e)}")