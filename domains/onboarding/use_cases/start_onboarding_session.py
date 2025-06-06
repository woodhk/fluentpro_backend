"""
Start onboarding session use case.

Handles initialization of the onboarding process for users.
"""

import logging

from core.exceptions import (
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from onboarding.models.onboarding import OnboardingFlow
from infrastructure.persistence.supabase.client import ISupabaseClient
from domains.onboarding.services.interfaces import IOnboardingService

logger = logging.getLogger(__name__)


class StartOnboardingSession:
    """
    Use case for starting an onboarding session.
    
    Initializes or retrieves the onboarding flow for a user
    and sets up the appropriate starting point based on progress.
    """
    
    def __init__(
        self,
        database_client: ISupabaseClient
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            database_client: Supabase client for data operations
        """
        self.database_client = database_client
    
    def execute(self, user_id: str) -> OnboardingFlow:
        """
        Execute onboarding session startup.
        
        Args:
            user_id: User ID to start onboarding for
            
        Returns:
            OnboardingFlow instance with current progress
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If flow creation fails
        """
        try:
            # Get user profile to determine current onboarding status
            user_response = self.database_client.table('users')\
                .select('id, auth0_id, onboarding_status, native_language, industry_id, selected_role_id')\
                .eq('id', user_id)\
                .execute()
            
            if not user_response.data:
                raise SupabaseUserNotFoundError(user_id)
            
            user_data = user_response.data[0]
            
            # Determine current phase based on user data
            current_phase = self._determine_current_phase(user_data)
            
            # Create onboarding flow
            flow = OnboardingFlow(
                user_id=user_id,
                current_phase=current_phase
            )
            
            # Update step statuses based on user progress
            self._update_flow_from_user_data(flow, user_data)
            
            return flow
            
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