"""
Communication partner repository implementation using Supabase.
Concrete implementation of IPartnerRepository for data persistence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from domains.onboarding.repositories.interfaces import IPartnerRepository
from domains.onboarding.models.communication_partner import (
    CommunicationPartner,
    Unit,
    UserCommunicationPartnerSelection,
    UserUnitSelection,
    UserCommunicationNeed
)
from domains.shared.repositories.base_repository import BaseRepository
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class PartnerRepositoryImpl(BaseRepository[CommunicationPartner, str], IPartnerRepository):
    """
    Concrete implementation of IPartnerRepository using Supabase.
    Handles communication partner and unit operations.
    """
    
    def __init__(self, supabase_client):
        super().__init__('communication_partners')
        self.client = supabase_client
    
    async def find_by_id(self, id: str) -> Optional[CommunicationPartner]:
        """Find communication partner by ID."""
        try:
            response = await self.client.table(self.table_name)\
                .select('*')\
                .eq('id', id)\
                .eq('is_active', True)\
                .execute()
            
            if not response.data:
                return None
            
            return self._to_entity(response.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get communication partner by ID {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication partner: {str(e)}")
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[CommunicationPartner]:
        """Find all communication partners matching filters."""
        try:
            query = self.client.table(self.table_name)\
                .select('*')\
                .eq('is_active', True)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = await query.order('sort_order').execute()
            return [self._to_entity(partner_data) for partner_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get communication partners with filters {filters}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication partners: {str(e)}")
    
    async def save(self, entity: CommunicationPartner) -> CommunicationPartner:
        """Save entity (create or update)."""
        try:
            data = self._to_dict(entity)
            
            if entity.id:
                # Update existing partner
                response = await self.client.table(self.table_name)\
                    .update(data)\
                    .eq('id', entity.id)\
                    .execute()
                
                if not response.data:
                    raise ResourceNotFoundError("CommunicationPartner", entity.id)
                
                return self._to_entity(response.data[0])
            else:
                # Create new partner
                data['created_at'] = datetime.utcnow().isoformat()
                response = await self.client.table(self.table_name)\
                    .insert(data)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("Communication partner creation failed - no data returned")
                
                return self._to_entity(response.data[0])
                
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to save communication partner: {str(e)}")
            raise DatabaseError(f"Communication partner save failed: {str(e)}")
    
    async def delete(self, id: str) -> bool:
        """Delete communication partner by ID (soft delete)."""
        try:
            response = await self.client.table(self.table_name)\
                .update({'is_active': False})\
                .eq('id', id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to delete communication partner {id}: {str(e)}")
            raise DatabaseError(f"Communication partner deletion failed: {str(e)}")
    
    async def get_partners(self) -> List[CommunicationPartner]:
        """Get all active communication partners."""
        return await self.find_all()
    
    async def get_units(self) -> List[Unit]:
        """Get all active communication units."""
        try:
            response = await self.client.table('units')\
                .select('*')\
                .eq('is_active', True)\
                .order('sort_order')\
                .execute()
            
            return [Unit.from_supabase_data(unit_data) for unit_data in response.data]
            
        except Exception as e:
            logger.error(f"Failed to get communication units: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication units: {str(e)}")
    
    async def get_user_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """Get user's selected partners."""
        try:
            response = await self.client.table('user_communication_partner_selections')\
                .select('*, communication_partners(name)')\
                .eq('user_id', user_id)\
                .order('priority')\
                .execute()
            
            selections = []
            for data in response.data:
                # Extract partner name from joined data
                partner_name = data.get('communication_partners', {}).get('name', '')
                
                selection = UserCommunicationPartnerSelection(
                    user_id=data['user_id'],
                    communication_partner_id=data['communication_partner_id'],
                    partner_name=partner_name,
                    priority=data['priority'],
                    is_custom=data.get('is_custom', False),
                    custom_partner_name=data.get('custom_partner_name'),
                    custom_partner_description=data.get('custom_partner_description'),
                    selected_at=datetime.fromisoformat(data['selected_at'].replace('Z', '+00:00')) if data.get('selected_at') else None
                )
                selections.append(selection)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to get user partners for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user partners: {str(e)}")
    
    async def get_user_units(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """Get user's selected units for a partner."""
        try:
            response = await self.client.table('user_unit_selections')\
                .select('*, units(name)')\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .order('priority')\
                .execute()
            
            selections = []
            for data in response.data:
                # Extract unit name from joined data
                unit_name = data.get('units', {}).get('name', data.get('unit_name', ''))
                
                selection = UserUnitSelection(
                    user_id=data['user_id'],
                    communication_partner_id=data['communication_partner_id'],
                    unit_id=data.get('unit_id'),
                    unit_name=unit_name,
                    priority=data['priority'],
                    is_custom=data.get('is_custom', False),
                    custom_unit_name=data.get('custom_unit_name'),
                    custom_unit_description=data.get('custom_unit_description'),
                    selected_at=datetime.fromisoformat(data['selected_at'].replace('Z', '+00:00')) if data.get('selected_at') else None
                )
                selections.append(selection)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to get user units for {user_id}, partner {partner_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user units: {str(e)}")
    
    async def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """Save user's partner selections."""
        try:
            # First, delete existing selections
            await self.client.table('user_communication_partner_selections')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            selections_data = []
            
            # Add regular partner selections
            for priority, partner_id in enumerate(partner_ids, 1):
                selections_data.append({
                    'user_id': user_id,
                    'communication_partner_id': partner_id,
                    'priority': priority,
                    'is_custom': False,
                    'selected_at': datetime.utcnow().isoformat()
                })
            
            # Add custom partner selections
            if custom_partners:
                for partner_name in custom_partners:
                    if partner_name.strip():
                        selections_data.append({
                            'user_id': user_id,
                            'communication_partner_id': 'custom',  # Placeholder ID for custom partners
                            'priority': len(selections_data) + 1,
                            'is_custom': True,
                            'custom_partner_name': partner_name.strip(),
                            'selected_at': datetime.utcnow().isoformat()
                        })
            
            if selections_data:
                response = await self.client.table('user_communication_partner_selections')\
                    .insert(selections_data)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("Failed to save partner selections")
            
            # Return updated selections
            return await self.get_user_partners(user_id)
            
        except Exception as e:
            logger.error(f"Failed to save partner selections for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to save partner selections: {str(e)}")
    
    async def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """Save user's unit selections for a partner."""
        try:
            # First, delete existing selections for this partner
            await self.client.table('user_unit_selections')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            selections_data = []
            
            # Add regular unit selections
            for priority, unit_id in enumerate(unit_ids, 1):
                selections_data.append({
                    'user_id': user_id,
                    'communication_partner_id': partner_id,
                    'unit_id': unit_id,
                    'priority': priority,
                    'is_custom': False,
                    'selected_at': datetime.utcnow().isoformat()
                })
            
            # Add custom unit selections
            if custom_units:
                for unit_name in custom_units:
                    if unit_name.strip():
                        selections_data.append({
                            'user_id': user_id,
                            'communication_partner_id': partner_id,
                            'unit_id': None,
                            'priority': len(selections_data) + 1,
                            'is_custom': True,
                            'custom_unit_name': unit_name.strip(),
                            'selected_at': datetime.utcnow().isoformat()
                        })
            
            if selections_data:
                response = await self.client.table('user_unit_selections')\
                    .insert(selections_data)\
                    .execute()
                
                if not response.data:
                    raise DatabaseError("Failed to save unit selections")
            
            # Return updated selections
            return await self.get_user_units(user_id, partner_id)
            
        except Exception as e:
            logger.error(f"Failed to save unit selections for {user_id}, partner {partner_id}: {str(e)}")
            raise DatabaseError(f"Failed to save unit selections: {str(e)}")
    
    async def get_user_communication_needs(self, user_id: str) -> UserCommunicationNeed:
        """Get complete communication needs for a user."""
        try:
            partner_selections = await self.get_user_partners(user_id)
            
            # Get all unit selections for all partners
            all_unit_selections = []
            for partner in partner_selections:
                units = await self.get_user_units(user_id, partner.communication_partner_id)
                all_unit_selections.extend(units)
            
            return UserCommunicationNeed(
                user_id=user_id,
                partner_selections=partner_selections,
                unit_selections=all_unit_selections
            )
            
        except Exception as e:
            logger.error(f"Failed to get communication needs for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication needs: {str(e)}")
    
    async def get_partner_statistics(self) -> Dict[str, Any]:
        """Get communication partner usage statistics."""
        try:
            # Total partners
            total_response = await self.client.table(self.table_name)\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Most popular partners
            popular_response = await self.client.table('user_communication_partner_selections')\
                .select('communication_partner_id, communication_partners(name)', count='exact')\
                .execute()
            
            # Count selections by partner
            partner_counts = {}
            for selection in popular_response.data:
                partner_id = selection['communication_partner_id']
                partner_name = selection.get('communication_partners', {}).get('name', 'Custom')
                
                if partner_id in partner_counts:
                    partner_counts[partner_id]['count'] += 1
                else:
                    partner_counts[partner_id] = {
                        'name': partner_name,
                        'count': 1
                    }
            
            # Sort by popularity
            most_popular = sorted(
                partner_counts.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5]
            
            return {
                'total_partners': total_response.count,
                'total_selections': len(popular_response.data),
                'most_popular': [
                    {
                        'partner_id': partner_id,
                        'name': data['name'],
                        'selection_count': data['count']
                    }
                    for partner_id, data in most_popular
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get partner statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve partner statistics: {str(e)}")
    
    async def get_unit_statistics(self) -> Dict[str, Any]:
        """Get communication unit usage statistics."""
        try:
            # Total units
            total_response = await self.client.table('units')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Most popular units
            popular_response = await self.client.table('user_unit_selections')\
                .select('unit_id, units(name)', count='exact')\
                .execute()
            
            # Count selections by unit
            unit_counts = {}
            for selection in popular_response.data:
                unit_id = selection['unit_id'] or 'custom'
                unit_name = selection.get('units', {}).get('name', 'Custom')
                
                if unit_id in unit_counts:
                    unit_counts[unit_id]['count'] += 1
                else:
                    unit_counts[unit_id] = {
                        'name': unit_name,
                        'count': 1
                    }
            
            # Sort by popularity
            most_popular = sorted(
                unit_counts.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5]
            
            return {
                'total_units': total_response.count,
                'total_selections': len(popular_response.data),
                'most_popular': [
                    {
                        'unit_id': unit_id,
                        'name': data['name'],
                        'selection_count': data['count']
                    }
                    for unit_id, data in most_popular
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get unit statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve unit statistics: {str(e)}")
    
    def _to_entity(self, data: Dict[str, Any]) -> CommunicationPartner:
        """Convert database row to CommunicationPartner entity."""
        return CommunicationPartner.from_supabase_data(data)
    
    def _to_dict(self, entity: CommunicationPartner) -> Dict[str, Any]:
        """Convert CommunicationPartner entity to database row."""
        return {
            'name': entity.name,
            'description': entity.description,
            'partner_type': entity.partner_type.value,
            'is_active': entity.is_active,
            'sort_order': entity.sort_order,
        }