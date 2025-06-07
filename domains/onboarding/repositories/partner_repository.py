"""
Partner repository implementation using Supabase.
Handles communication partner and unit data access operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from domains.onboarding.repositories.interfaces import IPartnerRepository
from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseError,
    SupabaseUserNotFoundError
)
from onboarding.models.communication import (
    CommunicationPartner,
    Unit,
    UserCommunicationPartnerSelection,
    UserUnitSelection,
    UserCommunicationNeed
)
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class PartnerRepository(IPartnerRepository):
    """
    Concrete implementation of IPartnerRepository using Supabase.
    Handles communication partner and unit data operations.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase = supabase_service or SupabaseService()
    
    def get_partners(self) -> List[CommunicationPartner]:
        """Get all active communication partners."""
        try:
            response = self.supabase.client.table('communication_partners')\
                .select('*')\
                .eq('is_active', True)\
                .order('sort_order, name')\
                .execute()
            
            partners = []
            for partner_data in response.data:
                partner = CommunicationPartner.from_supabase_data(partner_data)
                partners.append(partner)
            
            return partners
            
        except Exception as e:
            logger.error(f"Failed to get communication partners: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication partners: {str(e)}")
    
    def get_units(self) -> List[Unit]:
        """Get all active communication units."""
        try:
            response = self.supabase.client.table('units')\
                .select('*')\
                .eq('is_active', True)\
                .order('sort_order, name')\
                .execute()
            
            units = []
            for unit_data in response.data:
                unit = Unit.from_supabase_data(unit_data)
                units.append(unit)
            
            return units
            
        except Exception as e:
            logger.error(f"Failed to get communication units: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication units: {str(e)}")
    
    def get_user_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """Get user's selected partners."""
        try:
            response = self.supabase.client.table('user_communication_partners')\
                .select('*, communication_partners(id, name, description)')\
                .eq('user_id', user_id)\
                .order('priority')\
                .execute()
            
            selections = []
            for item in response.data:
                partner_info = item.get('communication_partners', {})
                selection = UserCommunicationPartnerSelection(
                    user_id=user_id,
                    communication_partner_id=partner_info.get('id', ''),
                    partner_name=partner_info.get('name', ''),
                    priority=item['priority'],
                    is_custom=False,
                    selected_at=datetime.fromisoformat(
                        item.get('created_at', datetime.utcnow().isoformat())
                    )
                )
                selections.append(selection)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to get user partners for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user communication partners: {str(e)}")
    
    def get_user_units(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """Get user's selected units for a partner."""
        try:
            response = self.supabase.client.table('user_partner_units')\
                .select('*, units(id, name, description)')\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .order('priority')\
                .execute()
            
            selections = []
            for item in response.data:
                if item['is_custom']:
                    selection = UserUnitSelection(
                        user_id=user_id,
                        communication_partner_id=partner_id,
                        unit_id=None,
                        unit_name=item['custom_unit_name'],
                        priority=item['priority'],
                        is_custom=True,
                        custom_unit_name=item['custom_unit_name'],
                        custom_unit_description=item['custom_unit_description'],
                        selected_at=datetime.fromisoformat(
                            item.get('created_at', datetime.utcnow().isoformat())
                        )
                    )
                else:
                    unit_info = item.get('units', {})
                    selection = UserUnitSelection(
                        user_id=user_id,
                        communication_partner_id=partner_id,
                        unit_id=unit_info.get('id', ''),
                        unit_name=unit_info.get('name', ''),
                        priority=item['priority'],
                        is_custom=False,
                        selected_at=datetime.fromisoformat(
                            item.get('created_at', datetime.utcnow().isoformat())
                        )
                    )
                selections.append(selection)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to get user units for {user_id}, partner {partner_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user units: {str(e)}")
    
    def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """Save user's partner selections."""
        try:
            if not partner_ids and not custom_partners:
                raise ValidationError("At least one communication partner must be selected")
            
            # Verify user exists
            user_check = self.supabase.client.table('users')\
                .select('id')\
                .eq('id', user_id)\
                .execute()
            
            if not user_check.data:
                raise SupabaseUserNotFoundError(user_id)
            
            # Validate partner IDs exist
            if partner_ids:
                partners_response = self.supabase.client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_partner_ids = [p['id'] for p in partners_response.data]
                invalid_ids = [pid for pid in partner_ids if pid not in valid_partner_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid partner IDs: {invalid_ids}")
            
            # Clear existing selections
            self.supabase.client.table('user_communication_partners')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            # Store new selections
            selections = []
            priority = 1
            
            # Store database partners
            if partner_ids:
                partners_response = self.supabase.client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .execute()
                
                for partner_id in partner_ids:
                    partner_info = next(p for p in partners_response.data if p['id'] == partner_id)
                    
                    # Insert into database
                    insert_result = self.supabase.client.table('user_communication_partners').insert({
                        'user_id': user_id,
                        'communication_partner_id': partner_id,
                        'priority': priority
                    }).execute()
                    
                    if insert_result.data:
                        selection = UserCommunicationPartnerSelection(
                            user_id=user_id,
                            communication_partner_id=partner_id,
                            partner_name=partner_info['name'],
                            priority=priority,
                            is_custom=False,
                            selected_at=datetime.utcnow()
                        )
                        selections.append(selection)
                        priority += 1
            
            # Note: Custom partners would need additional table structure
            # For now, we'll track them in the response but not persist separately
            if custom_partners:
                for custom_name in custom_partners:
                    if custom_name.strip():
                        selection = UserCommunicationPartnerSelection(
                            user_id=user_id,
                            communication_partner_id="",  # No ID for custom
                            partner_name=custom_name.strip(),
                            priority=priority,
                            is_custom=True,
                            custom_partner_name=custom_name.strip(),
                            selected_at=datetime.utcnow()
                        )
                        selections.append(selection)
                        priority += 1
            
            return selections
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Partner selection failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to save partner selections: {str(e)}")
            raise DatabaseError(f"Partner selection failed: {str(e)}")
    
    def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """Save user's unit selections for a partner."""
        try:
            if not unit_ids and not custom_units:
                raise ValidationError("At least one unit must be selected")
            
            # Validate partner belongs to user
            partner_check = self.supabase.client.table('user_communication_partners')\
                .select('communication_partner_id')\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            if not partner_check.data:
                raise ResourceNotFoundError("Communication Partner", partner_id)
            
            # Validate unit IDs exist
            if unit_ids:
                units_response = self.supabase.client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_unit_ids = [u['id'] for u in units_response.data]
                invalid_ids = [uid for uid in unit_ids if uid not in valid_unit_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid unit IDs: {invalid_ids}")
            
            # Clear existing units for this partner
            self.supabase.client.table('user_partner_units')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            # Store new selections
            selections = []
            priority = 1
            
            # Store database units
            if unit_ids:
                units_response = self.supabase.client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .execute()
                
                for unit_id in unit_ids:
                    unit_info = next(u for u in units_response.data if u['id'] == unit_id)
                    
                    # Insert into database
                    insert_result = self.supabase.client.table('user_partner_units').insert({
                        'user_id': user_id,
                        'communication_partner_id': partner_id,
                        'unit_id': unit_id,
                        'priority': priority,
                        'is_custom': False
                    }).execute()
                    
                    if insert_result.data:
                        selection = UserUnitSelection(
                            user_id=user_id,
                            communication_partner_id=partner_id,
                            unit_id=unit_id,
                            unit_name=unit_info['name'],
                            priority=priority,
                            is_custom=False,
                            selected_at=datetime.utcnow()
                        )
                        selections.append(selection)
                        priority += 1
            
            # Store custom units
            if custom_units:
                for custom_name in custom_units:
                    if custom_name.strip():
                        # Insert custom unit
                        insert_result = self.supabase.client.table('user_partner_units').insert({
                            'user_id': user_id,
                            'communication_partner_id': partner_id,
                            'unit_id': None,  # NULL for custom units
                            'priority': priority,
                            'is_custom': True,
                            'custom_unit_name': custom_name.strip(),
                            'custom_unit_description': f"Custom communication situation: {custom_name.strip()}"
                        }).execute()
                        
                        if insert_result.data:
                            selection = UserUnitSelection(
                                user_id=user_id,
                                communication_partner_id=partner_id,
                                unit_id=None,
                                unit_name=custom_name.strip(),
                                priority=priority,
                                is_custom=True,
                                custom_unit_name=custom_name.strip(),
                                custom_unit_description=f"Custom communication situation: {custom_name.strip()}",
                                selected_at=datetime.utcnow()
                            )
                            selections.append(selection)
                            priority += 1
            
            return selections
            
        except (ValidationError, ResourceNotFoundError) as e:
            logger.warning(f"Unit selection failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to save unit selections: {str(e)}")
            raise DatabaseError(f"Unit selection failed: {str(e)}")
    
    def get_user_communication_needs(self, user_id: str) -> UserCommunicationNeed:
        """Get complete communication needs for a user."""
        try:
            # Get partner selections
            partner_selections = self.get_user_partners(user_id)
            
            # Get unit selections for all partners
            unit_selections = []
            for partner_selection in partner_selections:
                partner_units = self.get_user_units(user_id, partner_selection.communication_partner_id)
                unit_selections.extend(partner_units)
            
            return UserCommunicationNeed(
                user_id=user_id,
                partner_selections=partner_selections,
                unit_selections=unit_selections
            )
            
        except Exception as e:
            logger.error(f"Failed to get user communication needs: {str(e)}")
            raise DatabaseError(f"Failed to retrieve communication needs: {str(e)}")
    
    def get_partner_statistics(self) -> Dict[str, Any]:
        """Get communication partner usage statistics."""
        try:
            # Total partners
            total_response = self.supabase.client.table('communication_partners')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Partner selections
            selections_response = self.supabase.client.table('user_communication_partners')\
                .select('communication_partner_id')\
                .execute()
            
            # Count selections per partner
            partner_counts = {}
            for selection in selections_response.data:
                partner_id = selection['communication_partner_id']
                partner_counts[partner_id] = partner_counts.get(partner_id, 0) + 1
            
            # Most popular partners
            most_popular = sorted(
                partner_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                'total_partners': total_response.count,
                'partners_selected': len(partner_counts),
                'total_selections': len(selections_response.data),
                'most_popular_partners': [
                    {'partner_id': partner_id, 'selection_count': count}
                    for partner_id, count in most_popular
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get partner statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve partner statistics: {str(e)}")
    
    def get_unit_statistics(self) -> Dict[str, Any]:
        """Get communication unit usage statistics."""
        try:
            # Total units
            total_response = self.supabase.client.table('units')\
                .select('id', count='exact')\
                .eq('is_active', True)\
                .execute()
            
            # Unit selections
            selections_response = self.supabase.client.table('user_partner_units')\
                .select('unit_id, is_custom')\
                .execute()
            
            # Count selections
            unit_counts = {}
            custom_units_count = 0
            
            for selection in selections_response.data:
                if selection['is_custom']:
                    custom_units_count += 1
                else:
                    unit_id = selection['unit_id']
                    if unit_id:
                        unit_counts[unit_id] = unit_counts.get(unit_id, 0) + 1
            
            # Most popular units
            most_popular = sorted(
                unit_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                'total_units': total_response.count,
                'units_selected': len(unit_counts),
                'custom_units_created': custom_units_count,
                'total_selections': len(selections_response.data),
                'most_popular_units': [
                    {'unit_id': unit_id, 'selection_count': count}
                    for unit_id, count in most_popular
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get unit statistics: {str(e)}")
            raise DatabaseError(f"Failed to retrieve unit statistics: {str(e)}")