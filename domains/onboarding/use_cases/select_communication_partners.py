"""
Communication partners selection use case.

Handles user's selection of communication partners during onboarding.
"""

from typing import List, Optional
from datetime import datetime
import logging

from core.patterns.use_case import UseCase
from core.exceptions import (
    ValidationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.onboarding.dto.requests import SelectCommunicationPartnersRequest
from domains.onboarding.dto.responses import OnboardingStepResponse, OnboardingStep
from onboarding.models.communication import UserCommunicationPartnerSelection
from domains.onboarding.repositories.interfaces import IPartnerRepository
from domains.authentication.repositories.interfaces import IUserRepository
from domains.onboarding.services.interfaces import IProfileSetupService

logger = logging.getLogger(__name__)


class SelectCommunicationPartnersUseCase(UseCase[SelectCommunicationPartnersRequest, OnboardingStepResponse]):
    """
    Use case for selecting communication partners.
    
    Handles selection of who the user typically communicates
    with in English at work (e.g., clients, colleagues, stakeholders).
    """
    
    def __init__(
        self,
        partner_repository: IPartnerRepository,
        user_repository: IUserRepository,
        profile_service: IProfileSetupService
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            partner_repository: Repository for partner data operations
            user_repository: Repository for user data operations
            profile_service: Profile setup service for business logic
        """
        self.partner_repository = partner_repository
        self.user_repository = user_repository
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
    
    async def execute(
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
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise SupabaseUserNotFoundError(user_id)
            
            # Resolve partner IDs (handles both UUIDs and slugs)
            if partner_ids:
                partner_ids = await self._resolve_partner_ids(partner_ids)
                
                # Validate resolved partner IDs exist
                partners = await self.partner_repository.get_partners()
                valid_partner_ids = [p['id'] for p in partners if p['id'] in partner_ids and p.get('is_active', True)]
                invalid_ids = [pid for pid in partner_ids if pid not in valid_partner_ids]
                
                if invalid_ids:
                    raise ValidationError(f"Invalid partner IDs: {invalid_ids}")
            
            # Save partner selections using repository
            selections = await self.partner_repository.save_partner_selections(
                user_id=user_id,
                partner_ids=partner_ids or [],
                custom_partners=custom_partners
            )
            
            # Convert to domain objects
            result_selections = []
            priority = 1
            
            for selection_data in selections:
                selection = UserCommunicationPartnerSelection(
                    user_id=user_id,
                    communication_partner_id=selection_data.get('communication_partner_id', ''),
                    partner_name=selection_data.get('partner_name', ''),
                    priority=priority,
                    is_custom=selection_data.get('is_custom', False),
                    custom_partner_name=selection_data.get('custom_partner_name'),
                    selected_at=datetime.utcnow()
                )
                result_selections.append(selection)
                priority += 1
            
            return result_selections
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to select communication partners: {str(e)}")
            raise BusinessLogicError(f"Partner selection failed: {str(e)}")
    
    async def _resolve_partner_ids(self, partner_ids: List[str]) -> List[str]:
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
                
                # Query repository for the UUID by name
                partners = await self.partner_repository.get_partners()
                matching_partner = next((p for p in partners if p.get('name') == partner_name and p.get('is_active', True)), None)
                
                if not matching_partner:
                    raise ValidationError(f"Partner '{partner_name}' not found in database")
                
                resolved_ids.append(matching_partner['id'])
        
        return resolved_ids