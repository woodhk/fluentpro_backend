"""
Partner situations configuration use case.

Handles configuration of communication situations for each selected partner.
"""

from typing import List, Optional
from datetime import datetime
import logging

from core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError
)
from onboarding.models.communication import UserUnitSelection
from infrastructure.persistence.supabase.client import ISupabaseClient
from domains.onboarding.services.interfaces import IProfileSetupService

logger = logging.getLogger(__name__)


class ConfigurePartnerSituations:
    """
    Use case for configuring communication situations for partners.
    
    Handles selection of communication situations (units) for each
    communication partner (e.g., meetings, calls, presentations, negotiations).
    """
    
    def __init__(
        self,
        database_client: ISupabaseClient,
        profile_service: IProfileSetupService
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            database_client: Supabase client for data operations
            profile_service: Profile setup service for business logic
        """
        self.database_client = database_client
        self.profile_service = profile_service
        
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
    
    def execute(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """
        Execute partner situations configuration.
        
        Args:
            user_id: User ID
            partner_id: Communication partner ID
            unit_ids: List of unit IDs to select (can be UUIDs or slugs)
            custom_units: Optional list of custom unit names
            
        Returns:
            List of UserUnitSelection instances
            
        Raises:
            ValidationError: If selection data is invalid
            ResourceNotFoundError: If partner not found in user's selections
            BusinessLogicError: If configuration fails
        """
        try:
            if not unit_ids and not custom_units:
                raise ValidationError("At least one unit must be selected")
            
            # Validate partner belongs to user
            partner_check = self.database_client.table('user_communication_partners')\
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
                units_response = self.database_client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_unit_ids = [u['id'] for u in units_response.data]
                invalid_ids = [uid for uid in unit_ids if uid not in valid_unit_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid unit IDs: {invalid_ids}")
            
            # Clear existing units for this partner
            self.database_client.table('user_partner_units')\
                .delete()\
                .eq('user_id', user_id)\
                .eq('communication_partner_id', partner_id)\
                .execute()
            
            # Store selections
            selections = []
            priority = 1
            
            # Store database units
            if unit_ids:
                units_response = self.database_client.table('units')\
                    .select('id, name')\
                    .in_('id', unit_ids)\
                    .execute()
                
                for unit_id in unit_ids:
                    unit_info = next(u for u in units_response.data if u['id'] == unit_id)
                    
                    # Insert into database
                    insert_result = self.database_client.table('user_partner_units').insert({
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
                        insert_result = self.database_client.table('user_partner_units').insert({
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
            
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to configure partner situations: {str(e)}")
            raise BusinessLogicError(f"Situation configuration failed: {str(e)}")
    
    def _resolve_unit_ids(self, unit_ids: List[str]) -> List[str]:
        """
        Resolve unit identifiers to actual UUIDs.
        Handles both direct UUIDs and slug-based identifiers.
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
                unit_response = self.database_client.table('units')\
                    .select('id')\
                    .eq('name', unit_name)\
                    .eq('is_active', True)\
                    .execute()
                
                if not unit_response.data:
                    raise ValidationError(f"Unit '{unit_name}' not found in database")
                
                resolved_ids.append(unit_response.data[0]['id'])
        
        return resolved_ids