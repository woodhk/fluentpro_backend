"""
Business logic for communication partner and unit management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError,
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
from authentication.models.user import OnboardingStatus

logger = logging.getLogger(__name__)


class CommunicationManager:
    """
    Business logic manager for communication partner and unit operations.
    Handles communication needs collection and management.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()
        
        # Mapping from frontend slug identifiers to partner names
        self.PARTNER_SLUG_TO_NAME = {
            'senior-management': 'Senior Management',
            'customers': 'Customers', 
            'clients': 'Clients',
            'colleagues': 'Colleagues',
            'suppliers': 'Suppliers',
            'partners': 'Partners',
            'stakeholders': 'Stakeholders'
        }
        
        # Mapping from frontend slug identifiers to unit names
        self.UNIT_SLUG_TO_NAME = {
            'meetings': 'Meetings',
            'presentations': 'Presentations',
            'negotiations': 'Negotiations',
            'interviews': 'Interviews',
            'phone-calls': 'Phone Calls',
            'video-conferences': 'Video Conferences',
            'client-conversations': 'Client Conversations',
            'team-discussions': 'Team Discussions',
            'one-on-ones': 'One-on-Ones',
            'briefings': 'Briefings',
            'feedback-sessions': 'Feedback Sessions',
            'training-sessions': 'Training Sessions',
            'informal-chats': 'Informal Chats',
            'status-updates': 'Status Updates',
            'conflict-resolution': 'Conflict Resolution'
        }
    
    def _resolve_partner_ids(self, partner_ids: List[str]) -> List[str]:
        """
        Resolve partner identifiers to actual UUIDs.
        Handles both direct UUIDs and slug-based identifiers.
        
        Args:
            partner_ids: List of partner IDs (can be UUIDs or slugs)
            
        Returns:
            List of resolved UUID strings
            
        Raises:
            ValidationError: If any partner ID cannot be resolved
        """
        resolved_ids = []
        
        for partner_id in partner_ids:
            # Check if it's already a UUID (36 chars, contains hyphens)
            if len(partner_id) == 36 and '-' in partner_id:
                resolved_ids.append(partner_id)
            else:
                # Try to resolve slug to name, then name to UUID
                partner_name = self.PARTNER_SLUG_TO_NAME.get(partner_id)
                if not partner_name:
                    raise ValidationError(f"Unknown partner identifier: '{partner_id}'. Valid options: {list(self.PARTNER_SLUG_TO_NAME.keys())}")
                
                # Query database for the UUID by name
                partner_response = self.supabase_service.client.table('communication_partners')\
                    .select('id')\
                    .eq('name', partner_name)\
                    .eq('is_active', True)\
                    .execute()
                
                if not partner_response.data:
                    raise ValidationError(f"Partner '{partner_name}' not found in database")
                
                resolved_ids.append(partner_response.data[0]['id'])
        
        return resolved_ids
    
    def _resolve_unit_ids(self, unit_ids: List[str]) -> List[str]:
        """
        Resolve unit identifiers to actual UUIDs.
        Handles both direct UUIDs and slug-based identifiers.
        
        Args:
            unit_ids: List of unit IDs (can be UUIDs or slugs)
            
        Returns:
            List of resolved UUID strings
            
        Raises:
            ValidationError: If any unit ID cannot be resolved
        """
        resolved_ids = []
        
        for unit_id in unit_ids:
            # Check if it's already a UUID (36 chars, contains hyphens)
            if len(unit_id) == 36 and '-' in unit_id:
                resolved_ids.append(unit_id)
            else:
                # Try to resolve slug to name, then name to UUID
                unit_name = self.UNIT_SLUG_TO_NAME.get(unit_id)
                if not unit_name:
                    raise ValidationError(f"Unknown unit identifier: '{unit_id}'. Valid options: {list(self.UNIT_SLUG_TO_NAME.keys())}")
                
                # Query database for the UUID by name
                unit_response = self.supabase_service.client.table('units')\
                    .select('id')\
                    .eq('name', unit_name)\
                    .eq('is_active', True)\
                    .execute()
                
                if not unit_response.data:
                    raise ValidationError(f"Unit '{unit_name}' not found in database")
                
                resolved_ids.append(unit_response.data[0]['id'])
        
        return resolved_ids
    
    def get_available_communication_partners(self) -> List[CommunicationPartner]:
        """
        Get all available communication partners.
        
        Returns:
            List of CommunicationPartner instances
            
        Raises:
            BusinessLogicError: If retrieval fails
        """
        try:
            response = self.supabase_service.client.table('communication_partners')\
                .select('*')\
                .eq('is_active', True)\
                .order('name')\
                .execute()
            
            partners = []
            for partner_data in response.data:
                partner = CommunicationPartner.from_supabase_data(partner_data)
                partners.append(partner)
            
            return partners
            
        except Exception as e:
            logger.error(f"Failed to get communication partners: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve communication partners: {str(e)}")
    
    def get_available_units(self) -> List[Unit]:
        """
        Get all available communication units/situations.
        
        Returns:
            List of Unit instances
            
        Raises:
            BusinessLogicError: If retrieval fails
        """
        try:
            response = self.supabase_service.client.table('units')\
                .select('*')\
                .eq('is_active', True)\
                .order('name')\
                .execute()
            
            units = []
            for unit_data in response.data:
                unit = Unit.from_supabase_data(unit_data)
                units.append(unit)
            
            return units
            
        except Exception as e:
            logger.error(f"Failed to get communication units: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve communication units: {str(e)}")
    
    def select_communication_partners(
        self,
        user_id: str,
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """
        Select communication partners for a user.
        
        Args:
            user_id: User ID
            partner_ids: List of partner IDs to select
            custom_partners: Optional list of custom partner names
            
        Returns:
            List of UserCommunicationPartnerSelection instances
            
        Raises:
            ValidationError: If selection data is invalid
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If selection fails
        """
        try:
            if not partner_ids and not custom_partners:
                raise ValidationError("At least one communication partner must be selected")
            
            # Get user by ID (assuming user_id is the Supabase user ID)
            user_response = self.supabase_service.client.table('users')\
                .select('id, auth0_id')\
                .eq('id', user_id)\
                .execute()
            
            if not user_response.data:
                raise SupabaseUserNotFoundError(user_id)
            
            # Resolve partner IDs (handles both UUIDs and slugs)
            if partner_ids:
                partner_ids = self._resolve_partner_ids(partner_ids)
                
                # Validate resolved partner IDs exist
                partners_response = self.supabase_service.client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_partner_ids = [p['id'] for p in partners_response.data]
                invalid_ids = [pid for pid in partner_ids if pid not in valid_partner_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid partner IDs: {invalid_ids}")
            
            # Clear existing selections
            self.supabase_service.client.table('user_communication_partners')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            # Store selections
            selections = []
            priority = 1
            
            # Store database partners
            if partner_ids:
                partners_response = self.supabase_service.client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .execute()
                
                for partner_id in partner_ids:
                    partner_info = next(p for p in partners_response.data if p['id'] == partner_id)
                    
                    # Insert into database
                    insert_result = self.supabase_service.client.table('user_communication_partners').insert({
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
            logger.error(f"Failed to select communication partners: {str(e)}")
            raise BusinessLogicError(f"Partner selection failed: {str(e)}")
    
    def select_units_for_partner(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """
        Select communication units for a specific partner.
        
        Args:
            user_id: User ID
            partner_id: Communication partner ID
            unit_ids: List of unit IDs to select
            custom_units: Optional list of custom unit names
            
        Returns:
            List of UserUnitSelection instances
            
        Raises:
            ValidationError: If selection data is invalid
            ResourceNotFoundError: If partner not found in user's selections
            BusinessLogicError: If selection fails
        """
        try:
            if not unit_ids and not custom_units:
                raise ValidationError("At least one unit must be selected")
            
            # Validate partner belongs to user
            partner_check = self.supabase_service.client.table('user_communication_partners')\
                .select('communication_partner_id')\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            if not partner_check.data:
                raise ResourceNotFoundError("Communication Partner", partner_id)
            
            # Resolve unit IDs (handles both UUIDs and slugs)
            if unit_ids:
                unit_ids = self._resolve_unit_ids(unit_ids)
                
                # Validate resolved unit IDs exist
                units_response = self.supabase_service.client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_unit_ids = [u['id'] for u in units_response.data]
                invalid_ids = [uid for uid in unit_ids if uid not in valid_unit_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid unit IDs: {invalid_ids}")
            
            # Clear existing units for this partner
            self.supabase_service.client.table('user_partner_units')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            # Store selections
            selections = []
            priority = 1
            
            # Store database units
            if unit_ids:
                units_response = self.supabase_service.client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .execute()
                
                for unit_id in unit_ids:
                    unit_info = next(u for u in units_response.data if u['id'] == unit_id)
                    
                    # Insert into database
                    insert_result = self.supabase_service.client.table('user_partner_units').insert({
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
                        insert_result = self.supabase_service.client.table('user_partner_units').insert({
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
            logger.error(f"Failed to select units for partner: {str(e)}")
            raise BusinessLogicError(f"Unit selection failed: {str(e)}")
    
    def get_user_communication_needs(self, user_id: str) -> UserCommunicationNeed:
        """
        Get complete communication needs for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            UserCommunicationNeed instance with all selections
            
        Raises:
            BusinessLogicError: If retrieval fails
        """
        try:
            # Get partner selections
            partners_response = self.supabase_service.client.table('user_communication_partners')\
                .select('*, communication_partners(id, name, description)')\
                .eq('user_id', user_id)\
                .order('priority')\
                .execute()
            
            partner_selections = []
            for item in partners_response.data:
                selection = UserCommunicationPartnerSelection(
                    user_id=user_id,
                    communication_partner_id=item['communication_partners']['id'],
                    partner_name=item['communication_partners']['name'],
                    priority=item['priority'],
                    is_custom=False,
                    selected_at=datetime.fromisoformat(item.get('created_at', datetime.utcnow().isoformat()))
                )
                partner_selections.append(selection)
            
            # Get unit selections
            units_response = self.supabase_service.client.table('user_partner_units')\
                .select('*, units(id, name, description)')\
                .eq('user_id', user_id)\
                .order('communication_partner_id, priority')\
                .execute()
            
            unit_selections = []
            for item in units_response.data:
                if item['is_custom']:
                    selection = UserUnitSelection(
                        user_id=user_id,
                        communication_partner_id=item['communication_partner_id'],
                        unit_id=None,
                        unit_name=item['custom_unit_name'],
                        priority=item['priority'],
                        is_custom=True,
                        custom_unit_name=item['custom_unit_name'],
                        custom_unit_description=item['custom_unit_description'],
                        selected_at=datetime.fromisoformat(item.get('created_at', datetime.utcnow().isoformat()))
                    )
                else:
                    selection = UserUnitSelection(
                        user_id=user_id,
                        communication_partner_id=item['communication_partner_id'],
                        unit_id=item['units']['id'],
                        unit_name=item['units']['name'],
                        priority=item['priority'],
                        is_custom=False,
                        selected_at=datetime.fromisoformat(item.get('created_at', datetime.utcnow().isoformat()))
                    )
                unit_selections.append(selection)
            
            return UserCommunicationNeed(
                user_id=user_id,
                partner_selections=partner_selections,
                unit_selections=unit_selections
            )
            
        except Exception as e:
            logger.error(f"Failed to get user communication needs: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve communication needs: {str(e)}")
    
    def get_user_communication_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """
        Get user's selected communication partners.
        
        Args:
            user_id: User ID
            
        Returns:
            List of UserCommunicationPartnerSelection instances
        """
        try:
            communication_needs = self.get_user_communication_needs(user_id)
            return communication_needs.partner_selections
            
        except Exception as e:
            logger.error(f"Failed to get user communication partners: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve communication partners: {str(e)}")
    
    def get_units_for_partner(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """
        Get user's selected units for a specific partner.
        
        Args:
            user_id: User ID
            partner_id: Communication partner ID
            
        Returns:
            List of UserUnitSelection instances
        """
        try:
            communication_needs = self.get_user_communication_needs(user_id)
            return communication_needs.get_units_for_partner(partner_id)
            
        except Exception as e:
            logger.error(f"Failed to get units for partner: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve units for partner: {str(e)}")
    
    def get_communication_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about communication partners and units.
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            # Get partner statistics
            partners_response = self.supabase_service.client.table('communication_partners')\
                .select('*')\
                .execute()
            
            # Get unit statistics
            units_response = self.supabase_service.client.table('units')\
                .select('*')\
                .execute()
            
            # Get user selection statistics
            user_partners_response = self.supabase_service.client.table('user_communication_partners')\
                .select('communication_partner_id')\
                .execute()
            
            user_units_response = self.supabase_service.client.table('user_partner_units')\
                .select('unit_id, is_custom')\
                .execute()
            
            # Calculate statistics
            total_partners = len(partners_response.data)
            active_partners = len([p for p in partners_response.data if p.get('is_active', True)])
            
            total_units = len(units_response.data)
            active_units = len([u for u in units_response.data if u.get('is_active', True)])
            
            # Partner usage
            partner_usage = {}
            for selection in user_partners_response.data:
                partner_id = selection['communication_partner_id']
                partner_usage[partner_id] = partner_usage.get(partner_id, 0) + 1
            
            # Unit usage
            unit_usage = {}
            custom_units_count = 0
            for selection in user_units_response.data:
                if selection['is_custom']:
                    custom_units_count += 1
                else:
                    unit_id = selection['unit_id']
                    if unit_id:
                        unit_usage[unit_id] = unit_usage.get(unit_id, 0) + 1
            
            return {
                'partners': {
                    'total': total_partners,
                    'active': active_partners,
                    'usage_count': len(partner_usage),
                    'most_popular': max(partner_usage.items(), key=lambda x: x[1]) if partner_usage else None
                },
                'units': {
                    'total': total_units,
                    'active': active_units,
                    'usage_count': len(unit_usage),
                    'custom_units_created': custom_units_count,
                    'most_popular': max(unit_usage.items(), key=lambda x: x[1]) if unit_usage else None
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get communication statistics: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve statistics: {str(e)}")
    
    # Alias methods to match what the views expect
    def get_available_partners(self) -> List[CommunicationPartner]:
        """Alias for get_available_communication_partners."""
        return self.get_available_communication_partners()
    
    def get_user_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """Alias for get_user_communication_partners."""
        return self.get_user_communication_partners(user_id)
    
    def get_user_units(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """Alias for get_units_for_partner."""
        return self.get_units_for_partner(user_id, partner_id)
    
    def save_partner_selections(
        self,
        user_id: str,
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """
        Save partner selections and update session phase.
        Alias for select_communication_partners with session phase update.
        """
        try:
            # Call the main method
            selections = self.select_communication_partners(user_id, partner_ids, custom_partners)
            
            # Update session phase to course_assignment after communication partners are selected
            self._update_user_session_phase_after_partners(user_id)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to save partner selections: {str(e)}")
            raise
    
    def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """
        Save unit selections and potentially update session phase.
        Alias for select_units_for_partner with session phase update.
        """
        try:
            # Call the main method
            selections = self.select_units_for_partner(user_id, partner_id, unit_ids, custom_units)
            
            # Check if all partners have units selected and advance phase if needed
            self._check_and_advance_communication_phase(user_id)
            
            return selections
            
        except Exception as e:
            logger.error(f"Failed to save unit selections: {str(e)}")
            raise
    
    def _update_user_session_phase_after_partners(self, user_id: str) -> None:
        """
        Update user session phase after communication partners are selected.
        """
        try:
            # Get user auth0_id
            user_response = self.supabase_service.client.table('users')\
                .select('auth0_id')\
                .eq('id', user_id)\
                .execute()
            
            if not user_response.data:
                logger.warning(f"User not found for session phase update: {user_id}")
                return
            
            auth0_id = user_response.data[0]['auth0_id']
            
            # Update session phase to course_assignment (next phase after personalisation)
            self.supabase_service.client.table('user_sessions')\
                .update({'phase': 'course_assignment', 'updated_at': datetime.utcnow().isoformat()})\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            # Also update onboarding status
            self.supabase_service.client.table('users')\
                .update({'onboarding_status': OnboardingStatus.COURSE_ASSIGNMENT.value})\
                .eq('id', user_id)\
                .execute()
            
            logger.info(f"Updated session phase to 'course_assignment' and onboarding status for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update session phase after partner selection: {str(e)}")
    
    def _check_and_advance_communication_phase(self, user_id: str) -> None:
        """
        Check if communication setup is complete and advance to final phase if needed.
        """
        try:
            # Check if user has selected partners
            partners_response = self.supabase_service.client.table('user_communication_partners')\
                .select('communication_partner_id')\
                .eq('user_id', user_id)\
                .execute()
            
            if not partners_response.data:
                return  # No partners selected yet
            
            # Check if all partners have units selected
            partner_ids = [p['communication_partner_id'] for p in partners_response.data]
            
            for partner_id in partner_ids:
                units_response = self.supabase_service.client.table('user_partner_units')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .eq('communication_partner_id', partner_id)\
                    .execute()
                
                if not units_response.data:
                    return  # This partner doesn't have units yet, don't advance
            
            # All partners have units - advance to completed phase
            self.supabase_service.client.table('user_sessions')\
                .update({'phase': 'completed', 'updated_at': datetime.utcnow().isoformat()})\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            # Also update onboarding status to completed
            self.supabase_service.client.table('users')\
                .update({'onboarding_status': OnboardingStatus.COMPLETED.value})\
                .eq('id', user_id)\
                .execute()
            
            logger.info(f"Advanced user {user_id} to completed phase and status - all communication setup done")
            
        except Exception as e:
            logger.error(f"Failed to check communication phase completion: {str(e)}")