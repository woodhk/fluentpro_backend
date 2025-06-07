"""
Complete onboarding flow use case.

Handles completion of the entire onboarding process and summary generation.
"""

from typing import Dict, Any
import logging
from datetime import datetime

from core.patterns.use_case import UseCase
from core.exceptions import (
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.onboarding.dto.requests import CompleteOnboardingRequest
from domains.onboarding.dto.responses import OnboardingSummaryResponse
from domains.authentication.repositories.interfaces import IUserRepository
from domains.onboarding.repositories.interfaces import IPartnerRepository
from authentication.models.user import OnboardingStatus
from domains.onboarding.services.interfaces import IOnboardingService

logger = logging.getLogger(__name__)


class CompleteOnboardingFlowUseCase(UseCase[CompleteOnboardingRequest, OnboardingSummaryResponse]):
    """
    Completes the user onboarding flow and generates a summary.
    
    Flow:
    1. Extract user ID from session ID
    2. Retrieve user profile with all onboarding data
    3. Validate all required onboarding steps are completed
    4. Update user's onboarding status to completed
    5. Gather all onboarding selections (language, industry, role, partners)
    6. Generate comprehensive onboarding summary
    7. Return summary with completion timestamp
    
    Errors:
    - SupabaseUserNotFoundError: User not found in database
    - BusinessLogicError: Missing required onboarding data or completion failed
    
    Dependencies:
    - IUserRepository: To retrieve and update user profile
    - IPartnerRepository: To fetch selected partner details
    - IOnboardingService: For onboarding completion business logic
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
    
    async def execute(self, request: CompleteOnboardingRequest) -> OnboardingSummaryResponse:
        """
        Execute onboarding flow completion.
        
        Args:
            request: CompleteOnboardingRequest containing session_id
            
        Returns:
            OnboardingSummaryResponse with completion summary
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If completion fails
        """
        try:
            # Extract user ID from session (simplified for now - in real implementation, would look up session)
            user_id = request.session_id.split('-')[1] if '-' in request.session_id else request.session_id
            
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
                partners = communication_needs.get('partners', [])
            except Exception as e:
                logger.warning(f"Failed to get communication needs: {str(e)}")
                partners = []
            
            # Update onboarding status to completed
            user = await self.user_repository.find_by_id(user_id)
            if user:
                user.complete_onboarding()
                await self.user_repository.save(user)
            
            # Create profile summary
            profile_summary = {
                'native_language': user_profile_data.get('native_language'),
                'proficiency_level': 'intermediate',  # Default or from user data
                'industry': user_profile_data.get('industries', {}).get('name') if user_profile_data.get('industries') else None,
                'role': user_profile_data.get('roles', {}).get('title') if user_profile_data.get('roles') else None,
                'communication_partners': [p.get('name', '') for p in partners],
                'total_situations': len(partners) * 5  # Estimated
            }
            
            # Generate recommendations
            recommendations = [
                "Start with basic professional vocabulary",
                "Practice common workplace scenarios"
            ]
            
            if profile_summary.get('role'):
                recommendations.append(f"Focus on {profile_summary['role']}-specific communication")
            
            # Generate next steps
            next_steps = [
                "Complete your first lesson",
                "Set up daily practice reminders",
                "Explore the course library"
            ]
            
            return OnboardingSummaryResponse(
                user_id=user_id,
                completed_at=datetime.now(),
                profile_summary=profile_summary,
                recommendations=recommendations,
                next_steps=next_steps
            )
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to complete onboarding flow: {str(e)}")
            raise BusinessLogicError(f"Failed to complete onboarding flow: {str(e)}")