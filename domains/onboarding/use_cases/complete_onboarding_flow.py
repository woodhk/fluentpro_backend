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
from infrastructure.persistence.supabase.client import ISupabaseClient
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
        database_client: ISupabaseClient,
        onboarding_service: IOnboardingService
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            database_client: Supabase client for data operations
            onboarding_service: Onboarding service for business logic
        """
        self.database_client = database_client
        self.onboarding_service = onboarding_service
    
    def execute(self, user_id: str) -> Dict[str, Any]:
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
            user_profile_response = self.database_client.table('users')\
                .select('*, industries(name), roles(title)')\
                .eq('id', user_id)\
                .execute()
            
            if not user_profile_response.data:
                raise SupabaseUserNotFoundError(user_id)
                
            user_profile_data = user_profile_response.data[0]
            
            
            # Get communication needs
            try:
                partners_response = self.database_client.table('user_communication_partners')\
                    .select('*, communication_partners(name)')\
                    .eq('user_id', user_id)\
                    .execute()
                
                comm_data = {
                    'user_id': user_id,
                    'partners': [p['communication_partners']['name'] for p in partners_response.data]
                }
            except Exception as e:
                logger.warning(f"Failed to get communication needs: {str(e)}")
                comm_data = {'user_id': user_id, 'summary': {}, 'partners': [], 'units': []}
            
            # Update onboarding status to completed
            self.database_client.table('users')\
                .update({'onboarding_status': OnboardingStatus.COMPLETED.value})\
                .eq('id', user_id)\
                .execute()
            
            # Update session phase to completed
            self.database_client.table('user_sessions')\
                .update({'phase': 'completed'})\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
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