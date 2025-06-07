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
from domains.onboarding.repositories.interfaces import IPartnerRepository
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
    
    async def execute(
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
            user_partners = await self.partner_repository.get_user_partners(user_id)
            partner_exists = any(p.get('communication_partner_id') == partner_id for p in user_partners)
            
            if not partner_exists:
                raise ResourceNotFoundError("Communication Partner", partner_id)
            
            # Resolve unit IDs (handles both UUIDs and slugs)
            if unit_ids:
                unit_ids = await self._resolve_unit_ids(unit_ids)
                
                # Validate resolved unit IDs exist
                units = await self.partner_repository.get_units()
                valid_unit_ids = [u['id'] for u in units if u['id'] in unit_ids and u.get('is_active', True)]
                invalid_ids = [uid for uid in unit_ids if uid not in valid_unit_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid unit IDs: {invalid_ids}")
            
            # Save unit selections using repository
            selections = await self.partner_repository.save_unit_selections(
                user_id=user_id,
                partner_id=partner_id,
                unit_ids=unit_ids or [],
                custom_units=custom_units
            )
            
            # Convert to domain objects
            result_selections = []
            priority = 1
            
            for selection_data in selections:
                selection = UserUnitSelection(
                    user_id=user_id,
                    communication_partner_id=partner_id,
                    unit_id=selection_data.get('unit_id'),
                    unit_name=selection_data.get('unit_name', ''),
                    priority=priority,
                    is_custom=selection_data.get('is_custom', False),
                    custom_unit_name=selection_data.get('custom_unit_name'),
                    custom_unit_description=selection_data.get('custom_unit_description'),
                    selected_at=datetime.utcnow()
                )
                result_selections.append(selection)
                priority += 1
            
            return result_selections
            
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to configure partner situations: {str(e)}")
            raise BusinessLogicError(f"Situation configuration failed: {str(e)}")
    
    async def _resolve_unit_ids(self, unit_ids: List[str]) -> List[str]:
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
                
                # Query repository for the UUID by name
                units = await self.partner_repository.get_units()
                matching_unit = next((u for u in units if u.get('name') == unit_name and u.get('is_active', True)), None)
                
                if not matching_unit:
                    raise ValidationError(f"Unit '{unit_name}' not found in database")
                
                resolved_ids.append(matching_unit['id'])
        
        return resolved_ids