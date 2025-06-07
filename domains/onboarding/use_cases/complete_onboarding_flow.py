"""
Complete onboarding flow use case.

Handles completion of the entire onboarding process and summary generation.
"""

from typing import Dict, Any
import logging

from core.exceptions import (
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.authentication.repositories.interfaces import IUserRepository
from domains.onboarding.repositories.interfaces import IPartnerRepository
from authentication.models.user import OnboardingStatus
from domains.onboarding.services.interfaces import IOnboardingService

logger = logging.getLogger(__name__)


class CompleteOnboardingFlow:
    """
    Use case for completing the onboarding flow.
    
    Handles final onboarding completion, status updates,
    and comprehensive summary generation.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        partner_repository: IPartnerRepository,
        onboarding_service: IOnboardingService
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            user_repository: Repository for user data operations
            partner_repository: Repository for partner data operations
            onboarding_service: Onboarding service for business logic
        """
        self.user_repository = user_repository
        self.partner_repository = partner_repository
        self.onboarding_service = onboarding_service
    
    async def execute(self, user_id: str) -> Dict[str, Any]:
        """
        Execute onboarding flow completion.
        
        Args:
            user_id: User ID to complete onboarding for
            
        Returns:
            Dictionary with comprehensive onboarding summary
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If completion fails
        """
        try:
            # Get user profile with all onboarding data
            user_profile = await self.user_repository.get_profile(user_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(user_id)
            
            # Convert to dict format for compatibility
            user_profile_data = {
                'full_name': user_profile.full_name,
                'email': user_profile.email,
                'native_language': user_profile.native_language.value if user_profile.native_language else None,
                'industry_id': user_profile.industry_id,
                'selected_role_id': user_profile.selected_role_id,
                'industries': {'name': user_profile.industry_name} if user_profile.industry_name else None,
                'roles': {'title': user_profile.role_title} if user_profile.role_title else None
            }
            
            
            # Get communication needs
            try:
                communication_needs = await self.partner_repository.get_user_communication_needs(user_id)
                comm_data = {
                    'user_id': user_id,
                    'partners': communication_needs.get('partners', [])
                }
            except Exception as e:
                logger.warning(f"Failed to get communication needs: {str(e)}")
                comm_data = {'user_id': user_id, 'summary': {}, 'partners': [], 'units': []}
            
            # Update onboarding status to completed
            user = await self.user_repository.find_by_id(user_id)
            if user:
                user.complete_onboarding()
                await self.user_repository.save(user)
            
            return {
                'success': True,
                'user_profile': {
                    'name': user_profile_data.get('full_name'),
                    'email': user_profile_data.get('email'),
                    'native_language': user_profile_data.get('native_language'),
                    'industry': user_profile_data.get('industries', {}).get('name') if user_profile_data.get('industries') else None,
                    'role': user_profile_data.get('roles', {}).get('title') if user_profile_data.get('roles') else None,
                    'onboarding_status': 'completed'
                },
                'communication_needs': comm_data,
                'completion_summary': {
                    'basic_info_completed': user_profile_data.get('native_language') is not None,
                    'industry_selected': user_profile_data.get('industry_id') is not None,
                    'role_defined': user_profile_data.get('selected_role_id') is not None,
                    'communication_needs_defined': len(comm_data.get('partners', [])) > 0,
                    'ready_for_learning': True
                },
                'next_actions': ['Start your personalized learning journey'],
                'message': 'Onboarding completed successfully! You are now ready to begin your personalized English communication training.'
            }
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to complete onboarding flow: {str(e)}")
            raise BusinessLogicError(f"Failed to complete onboarding flow: {str(e)}")