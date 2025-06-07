"""
Communication partners selection use case.

Handles user's selection of communication partners during onboarding.
"""

from typing import List, Optional
from datetime import datetime
import logging

from core.exceptions import (
    ValidationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from onboarding.models.communication import UserCommunicationPartnerSelection
from domains.onboarding.repositories.interfaces import IPartnerRepository
from domains.onboarding.services.interfaces import IProfileSetupService

logger = logging.getLogger(__name__)


class SelectCommunicationPartners:
    """
    Use case for selecting communication partners.
    
    Handles selection of who the user typically communicates
    with in English at work (e.g., clients, colleagues, stakeholders).
    """
    
    def __init__(
        self,
        partner_repository: IPartnerRepository,
        profile_service: IProfileSetupService
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            partner_repository: Repository for partner data operations
            profile_service: Profile setup service for business logic
        """
        self.partner_repository = partner_repository
        self.profile_service = profile_service
        
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
    
    def execute(
        self,
        user_id: str,
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """
        Execute communication partners selection.
        
        Args:
            user_id: User ID
            partner_ids: List of partner IDs to select (can be UUIDs or slugs)
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
            
            # Get user by ID
            user_response = self.database_client.table('users')\
                .select('id, auth0_id')\
                .eq('id', user_id)\
                .execute()
            
            if not user_response.data:
                raise SupabaseUserNotFoundError(user_id)
            
            # Resolve partner IDs (handles both UUIDs and slugs)
            if partner_ids:
                partner_ids = self._resolve_partner_ids(partner_ids)
                
                # Validate resolved partner IDs exist
                partners_response = self.database_client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .eq('is_active', True)\
                    .execute()
                
                valid_partner_ids = [p['id'] for p in partners_response.data]
                invalid_ids = [pid for pid in partner_ids if pid not in valid_partner_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid partner IDs: {invalid_ids}")
            
            # Clear existing selections
            self.database_client.table('user_communication_partners')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            # Store selections
            selections = []
            priority = 1
            
            # Store database partners
            if partner_ids:
                partners_response = self.database_client.table('communication_partners')\
                    .select('id, name')\
                    .in_('id', partner_ids)\
                    .execute()
                
                for partner_id in partner_ids:
                    partner_info = next(p for p in partners_response.data if p['id'] == partner_id)
                    
                    # Insert into database
                    insert_result = self.database_client.table('user_communication_partners').insert({
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
            
            # Store custom partners (tracked in response but not persisted separately)
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
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to select communication partners: {str(e)}")
            raise BusinessLogicError(f"Partner selection failed: {str(e)}")
    
    def _resolve_partner_ids(self, partner_ids: List[str]) -> List[str]:
        """
        Resolve partner identifiers to actual UUIDs.
        Handles both direct UUIDs and slug-based identifiers.
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
                partner_response = self.database_client.table('communication_partners')\
                    .select('id')\
                    .eq('name', partner_name)\
                    .eq('is_active', True)\
                    .execute()
                
                if not partner_response.data:
                    raise ValidationError(f"Partner '{partner_name}' not found in database")
                
                resolved_ids.append(partner_response.data[0]['id'])
        
        return resolved_ids