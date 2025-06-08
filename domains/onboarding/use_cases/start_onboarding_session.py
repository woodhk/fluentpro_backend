"""
Start onboarding session use case.

Handles initialization of the onboarding process for users.
"""

import logging
from datetime import datetime, timedelta

from core.patterns.use_case import UseCase
from core.exceptions import (
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.onboarding.dto.requests import StartOnboardingRequest
from domains.onboarding.dto.responses import OnboardingSessionResponse, OnboardingStep, OnboardingSessionStatus
from onboarding.models.onboarding import OnboardingFlow
from domains.shared.repositories.interfaces import IUserRepository
from domains.onboarding.services.interfaces import IOnboardingService

logger = logging.getLogger(__name__)


class StartOnboardingSessionUseCase(UseCase[StartOnboardingRequest, OnboardingSessionResponse]):
    """
    Starts or resumes an onboarding session for a user.
    
    Flow:
    1. Retrieve user profile to check onboarding status
    2. Determine current onboarding phase from user data
    3. Create onboarding flow instance with progress
    4. Update flow steps based on completed items
    5. Generate session ID and calculate expiration
    6. Return session response with current step and progress
    
    Errors:
    - SupabaseUserNotFoundError: User not found in database
    - BusinessLogicError: Failed to create onboarding session
    
    Dependencies:
    - IUserRepository: To retrieve user profile and onboarding status
    """
    
    def __init__(
        self,
        user_repository: IUserRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            user_repository: Repository for user data operations
        """
        self.user_repository = user_repository
    
    async def execute(self, request: StartOnboardingRequest) -> OnboardingSessionResponse:
        """
        Execute onboarding session startup.
        
        Args:
            request: StartOnboardingRequest containing user_id
            
        Returns:
            OnboardingSessionResponse with session details
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If flow creation fails
        """
        try:
            # Get user profile to determine current onboarding status
            user_profile = await self.user_repository.get_profile(request.user_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(request.user_id)
            
            # Convert profile to dict format for compatibility with existing code
            user_data = {
                'id': user_profile.user_id,
                'auth0_id': user_profile.auth0_id,
                'onboarding_status': user_profile.onboarding_status.value if user_profile.onboarding_status else 'not_started',
                'native_language': user_profile.native_language.value if user_profile.native_language else None,
                'industry_id': user_profile.industry_id,
                'selected_role_id': user_profile.selected_role_id
            }
            
            # Determine current phase based on user data
            current_phase = self._determine_current_phase(user_data)
            
            # Create onboarding flow
            flow = OnboardingFlow(
                user_id=request.user_id,
                current_phase=current_phase
            )
            
            # Update step statuses based on user progress
            self._update_flow_from_user_data(flow, user_data)
            
            # Map to current step
            current_step = self._map_phase_to_step(current_phase)
            
            # Generate session ID
            session_id = f"session-{request.user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create progress mapping
            progress = {
                "language_selection": user_data.get('native_language') is not None,
                "industry_selection": user_data.get('industry_id') is not None,
                "role_selection": user_data.get('selected_role_id') is not None,
                "partner_selection": False,  # TODO: Check communication partners
                "situation_configuration": False  # TODO: Check situation configuration
            }
            
            return OnboardingSessionResponse(
                session_id=session_id,
                user_id=request.user_id,
                current_step=current_step,
                status=OnboardingSessionStatus.ACTIVE,
                started_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1),
                progress=progress
            )
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to start onboarding session: {str(e)}")
            raise BusinessLogicError(f"Failed to start onboarding session: {str(e)}")
    
    def _determine_current_phase(self, user_data):
        """Determine current onboarding phase based on user data."""
        from onboarding.models.onboarding import OnboardingPhase
        
        # Map database onboarding status to phase
        status_to_phase = {
            'not_started': OnboardingPhase.NOT_STARTED,
            'basic_info': OnboardingPhase.BASIC_INFO,
            'industry_selected': OnboardingPhase.INDUSTRY_SELECTION,
            'role_selected': OnboardingPhase.ROLE_SELECTION,
            'communication_needs': OnboardingPhase.COMMUNICATION_NEEDS,
            'completed': OnboardingPhase.COMPLETED
        }
        
        db_status = user_data.get('onboarding_status', 'not_started')
        return status_to_phase.get(db_status, OnboardingPhase.NOT_STARTED)
    
    def _update_flow_from_user_data(self, flow, user_data):
        """Update flow step statuses based on user progress."""
        # Mark steps as completed based on user data
        if user_data.get('native_language'):
            flow.complete_step('select_language', {'language': user_data['native_language']})
        
        if user_data.get('industry_id'):
            flow.complete_step('select_industry', {'industry_id': user_data['industry_id']})
        
        if user_data.get('selected_role_id'):
            flow.complete_step('role_selection', {'role_id': user_data['selected_role_id']})
            # Job input is implied if role is selected
            flow.complete_step('job_input', {'completed_via_role_selection': True})
    
    def _map_phase_to_step(self, phase) -> OnboardingStep:
        """Map onboarding phase to step enum."""
        from onboarding.models.onboarding import OnboardingPhase
        
        phase_to_step = {
            OnboardingPhase.NOT_STARTED: OnboardingStep.LANGUAGE_SELECTION,
            OnboardingPhase.BASIC_INFO: OnboardingStep.LANGUAGE_SELECTION,
            OnboardingPhase.INDUSTRY_SELECTION: OnboardingStep.INDUSTRY_SELECTION,
            OnboardingPhase.ROLE_SELECTION: OnboardingStep.ROLE_SELECTION,
            OnboardingPhase.COMMUNICATION_NEEDS: OnboardingStep.PARTNER_SELECTION,
            OnboardingPhase.COMPLETED: OnboardingStep.COMPLETION
        }
        
        return phase_to_step.get(phase, OnboardingStep.LANGUAGE_SELECTION)