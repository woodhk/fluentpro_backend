"""
Business logic for onboarding flow management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from core.exceptions import (
    ValidationError,
    BusinessLogicError,
    SupabaseUserNotFoundError
)
from onboarding.models.onboarding import (
    OnboardingFlow,
    OnboardingPhase,
    OnboardingStep,
    OnboardingStepStatus,
    UserSession
)
from authentication.models.user import OnboardingStatus
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class OnboardingManager:
    """
    Business logic manager for onboarding flow orchestration.
    Manages the complete onboarding process across multiple phases.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()
    
    def get_or_create_onboarding_flow(self, user_id: str) -> OnboardingFlow:
        """
        Get existing onboarding flow or create a new one.
        
        Args:
            user_id: User ID
            
        Returns:
            OnboardingFlow instance
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If flow creation fails
        """
        try:
            # Get user profile to determine current onboarding status
            user_response = self.supabase_service.client.table('users')\
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
            logger.error(f"Failed to get/create onboarding flow: {str(e)}")
            raise BusinessLogicError(f"Failed to create onboarding flow: {str(e)}")
    
    def complete_onboarding_step(
        self,
        user_id: str,
        step_id: str,
        step_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete an onboarding step and update user progress.
        
        Args:
            user_id: User ID
            step_id: Step ID to complete
            step_data: Optional data from the completed step
            
        Returns:
            Dictionary with updated flow information
            
        Raises:
            ValidationError: If step completion is invalid
            BusinessLogicError: If completion fails
        """
        try:
            # Get current onboarding flow
            flow = self.get_or_create_onboarding_flow(user_id)
            
            # Complete the step
            step_completed = flow.complete_step(step_id, step_data)
            if not step_completed:
                raise ValidationError(f"Step '{step_id}' not found or cannot be completed")
            
            # Update user's onboarding status in database
            self._update_user_onboarding_status(user_id, flow.current_phase)
            
            # Get updated flow
            updated_flow = self.get_or_create_onboarding_flow(user_id)
            
            response = {
                'success': True,
                'completed_step': step_id,
                'current_phase': updated_flow.current_phase.value,
                'progress_percentage': updated_flow.progress_percentage,
                'is_completed': updated_flow.is_completed,
                'next_step': updated_flow.next_step.to_dict() if updated_flow.next_step else None,
                'message': f"Step '{step_id}' completed successfully"
            }
            
            # Add phase completion message if applicable
            if updated_flow.is_completed:
                response['message'] = "Onboarding completed successfully!"
                response['celebration'] = True
            
            return response
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Step completion failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to complete onboarding step: {str(e)}")
            raise BusinessLogicError(f"Step completion failed: {str(e)}")
    
    def get_onboarding_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Get detailed onboarding progress for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with comprehensive progress information
        """
        try:
            flow = self.get_or_create_onboarding_flow(user_id)
            
            # Get user profile for additional context
            user_response = self.supabase_service.client.table('users')\
                .select('full_name, email, onboarding_status')\
                .eq('id', user_id)\
                .execute()
            
            user_info = user_response.data[0] if user_response.data else {}
            
            return {
                'user_info': {
                    'name': user_info.get('full_name'),
                    'email': user_info.get('email')
                },
                'onboarding_flow': flow.to_dict(),
                'phase_details': self._get_phase_details(flow),
                'recommendations': self._get_progress_recommendations(flow),
                'estimated_completion_time': self._estimate_completion_time(flow)
            }
            
        except Exception as e:
            logger.error(f"Failed to get onboarding progress: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve progress: {str(e)}")
    
    def skip_onboarding_step(
        self,
        user_id: str,
        step_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Skip an onboarding step (if allowed).
        
        Args:
            user_id: User ID
            step_id: Step ID to skip
            reason: Optional reason for skipping
            
        Returns:
            Dictionary with updated flow information
        """
        try:
            flow = self.get_or_create_onboarding_flow(user_id)
            
            # Skip the step
            step_skipped = flow.skip_step(step_id)
            if not step_skipped:
                raise ValidationError(f"Step '{step_id}' cannot be skipped or not found")
            
            # Log the skip reason if provided
            if reason:
                logger.info(f"User {user_id} skipped step {step_id}: {reason}")
            
            # Update user's onboarding status
            self._update_user_onboarding_status(user_id, flow.current_phase)
            
            return {
                'success': True,
                'skipped_step': step_id,
                'reason': reason,
                'current_phase': flow.current_phase.value,
                'progress_percentage': flow.progress_percentage,
                'next_step': flow.next_step.to_dict() if flow.next_step else None,
                'message': f"Step '{step_id}' skipped"
            }
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Step skip failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to skip onboarding step: {str(e)}")
            raise BusinessLogicError(f"Step skip failed: {str(e)}")
    
    def reset_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Reset user's onboarding progress.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with reset confirmation
        """
        try:
            # Reset user's onboarding status in database
            self.supabase_service.client.table('users')\
                .update({'onboarding_status': OnboardingStatus.NOT_STARTED.value})\
                .eq('id', user_id)\
                .execute()
            
            # Create fresh onboarding flow
            flow = OnboardingFlow(user_id=user_id)
            
            return {
                'success': True,
                'message': 'Onboarding reset successfully',
                'onboarding_flow': flow.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to reset onboarding: {str(e)}")
            raise BusinessLogicError(f"Onboarding reset failed: {str(e)}")
    
    def get_onboarding_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete onboarding summary including all collected data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with comprehensive onboarding summary
        """
        try:
            # Get user profile with all onboarding data
            user_profile_response = self.supabase_service.get_user_full_profile_by_user_id(user_id)
            
            if not user_profile_response:
                raise SupabaseUserNotFoundError(user_id)
            
            # Get communication needs
            from onboarding.business.communication_manager import CommunicationManager
            comm_manager = CommunicationManager(self.supabase_service)
            
            try:
                communication_needs = comm_manager.get_user_communication_needs(user_id)
                comm_data = communication_needs.to_dict()
            except Exception as e:
                logger.warning(f"Failed to get communication needs: {str(e)}")
                comm_data = {'user_id': user_id, 'summary': {}, 'partners': [], 'units': []}
            
            # Get onboarding flow progress
            flow = self.get_or_create_onboarding_flow(user_id)
            
            return {
                'user_profile': {
                    'name': user_profile_response.get('full_name'),
                    'email': user_profile_response.get('email'),
                    'native_language': user_profile_response.get('native_language'),
                    'industry': user_profile_response.get('industry_name'),
                    'role': user_profile_response.get('role_title'),
                    'onboarding_status': user_profile_response.get('onboarding_status')
                },
                'onboarding_progress': {
                    'current_phase': flow.current_phase.value,
                    'progress_percentage': flow.progress_percentage,
                    'is_completed': flow.is_completed,
                    'completed_steps': [
                        step.step_id for step in flow.steps 
                        if step.status == OnboardingStepStatus.COMPLETED
                    ]
                },
                'communication_needs': comm_data,
                'completion_summary': {
                    'basic_info_completed': user_profile_response.get('native_language') is not None,
                    'industry_selected': user_profile_response.get('industry_id') is not None,
                    'role_defined': user_profile_response.get('selected_role_id') is not None,
                    'communication_needs_defined': len(comm_data.get('partners', [])) > 0,
                    'ready_for_learning': flow.is_completed
                },
                'next_actions': self._get_summary_next_actions(flow, user_profile_response)
            }
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get onboarding summary: {str(e)}")
            raise BusinessLogicError(f"Failed to get onboarding summary: {str(e)}")
    
    def _determine_current_phase(self, user_data: Dict[str, Any]) -> OnboardingPhase:
        """Determine current onboarding phase based on user data."""
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
    
    def _update_flow_from_user_data(self, flow: OnboardingFlow, user_data: Dict[str, Any]) -> None:
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
    
    def _update_user_onboarding_status(self, user_id: str, phase: OnboardingPhase) -> None:
        """Update user's onboarding status in database."""
        # Map phase to database status
        phase_to_status = {
            OnboardingPhase.NOT_STARTED: 'not_started',
            OnboardingPhase.BASIC_INFO: 'basic_info',
            OnboardingPhase.INDUSTRY_SELECTION: 'industry_selected',
            OnboardingPhase.ROLE_SELECTION: 'role_selected',
            OnboardingPhase.COMMUNICATION_NEEDS: 'communication_needs',
            OnboardingPhase.COMPLETED: 'completed'
        }
        
        db_status = phase_to_status.get(phase, 'not_started')
        
        self.supabase_service.client.table('users')\
            .update({'onboarding_status': db_status})\
            .eq('id', user_id)\
            .execute()
    
    def _get_phase_details(self, flow: OnboardingFlow) -> Dict[str, Any]:
        """Get detailed information about each phase."""
        return {
            'current_phase': flow.current_phase.value,
            'phases': {
                phase.value: {
                    'name': phase.value.replace('_', ' ').title(),
                    'description': self._get_phase_description(phase),
                    'steps': [
                        step.to_dict() for step in flow.get_steps_for_phase(phase)
                    ],
                    'is_current': phase == flow.current_phase,
                    'is_completed': all(
                        step.is_completed for step in flow.get_steps_for_phase(phase)
                    ) if flow.get_steps_for_phase(phase) else False
                }
                for phase in OnboardingPhase
            }
        }
    
    def _get_phase_description(self, phase: OnboardingPhase) -> str:
        """Get description for an onboarding phase."""
        descriptions = {
            OnboardingPhase.NOT_STARTED: "Welcome to FluentPro! Let's get started.",
            OnboardingPhase.BASIC_INFO: "Tell us about your language preferences.",
            OnboardingPhase.INDUSTRY_SELECTION: "Select your industry for personalized content.",
            OnboardingPhase.ROLE_SELECTION: "Define your professional role and responsibilities.",
            OnboardingPhase.COMMUNICATION_NEEDS: "Identify your communication partners and situations.",
            OnboardingPhase.COMPLETED: "Great! Your profile is complete and ready for learning."
        }
        return descriptions.get(phase, "Onboarding phase")
    
    def _get_progress_recommendations(self, flow: OnboardingFlow) -> List[str]:
        """Get recommendations based on progress."""
        recommendations = []
        
        if flow.current_phase == OnboardingPhase.NOT_STARTED:
            recommendations.append("Start by selecting your native language")
        elif flow.current_phase == OnboardingPhase.BASIC_INFO:
            recommendations.append("Choose your industry to get relevant role suggestions")
        elif flow.current_phase == OnboardingPhase.INDUSTRY_SELECTION:
            recommendations.append("Describe your job role for personalized training")
        elif flow.current_phase == OnboardingPhase.ROLE_SELECTION:
            recommendations.append("Define who you communicate with at work")
        elif flow.current_phase == OnboardingPhase.COMMUNICATION_NEEDS:
            recommendations.append("Complete the final steps to start learning")
        else:
            recommendations.append("Start your personalized communication training")
        
        return recommendations
    
    def _estimate_completion_time(self, flow: OnboardingFlow) -> str:
        """Estimate time to complete onboarding."""
        remaining_steps = len([s for s in flow.steps if not s.is_completed])
        
        if remaining_steps == 0:
            return "Completed"
        elif remaining_steps <= 2:
            return "2-3 minutes"
        elif remaining_steps <= 4:
            return "5-7 minutes"
        else:
            return "8-10 minutes"
    
    def _get_summary_next_actions(self, flow: OnboardingFlow, user_data: Dict[str, Any]) -> List[str]:
        """Get next actions for summary."""
        if flow.is_completed:
            return ["Start your personalized learning journey"]
        
        actions = []
        if flow.next_step:
            actions.append(f"Complete: {flow.next_step.name}")
        
        return actions or ["Continue onboarding process"]