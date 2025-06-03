"""
Onboarding summary views for FluentPro v1.
Provides comprehensive onboarding status and data summary.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from authentication.business.user_manager import UserManager
from onboarding.business.communication_manager import CommunicationManager

logger = logging.getLogger(__name__)


class GetOnboardingSummaryView(CachedView, VersionedView):
    """
    Get complete onboarding summary endpoint.
    Shows all selected partners, units, and onboarding progress.
    """
    cache_timeout = 600  # 10 minutes cache
    
    def get(self, request):
        """Get complete onboarding summary."""
        try:
            auth0_id = self.get_auth0_user_id()
            
            # Check cache first
            cache_key = self.get_cache_key("summary", auth0_id)
            cached_summary = self.get_cached_response(cache_key)
            
            if cached_summary:
                return APIResponse.success(data=cached_summary)
            
            # Get current user profile
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(auth0_id)
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get communication selections
            communication_manager = CommunicationManager()
            user_partners = communication_manager.get_user_partners(user_profile.user.id)
            
            # Format communication partners
            partners = []
            partners_with_units = []
            all_units = []
            
            for partner_selection in user_partners:
                partner_info = {
                    'id': partner_selection.partner.id if partner_selection.partner else None,
                    'name': partner_selection.partner.name if partner_selection.partner else partner_selection.custom_partner_name,
                    'description': partner_selection.partner.description if partner_selection.partner else 'Custom partner',
                    'priority': partner_selection.priority,
                    'is_custom': partner_selection.is_custom
                }
                partners.append(partner_info)
                
                # Get units for this partner
                if partner_selection.partner:
                    unit_selections = communication_manager.get_user_units(
                        user_profile.user.id, 
                        partner_selection.partner.id
                    )
                    
                    partner_units = []
                    for unit_selection in unit_selections:
                        unit_info = {
                            'id': unit_selection.unit.id if unit_selection.unit else None,
                            'name': unit_selection.unit.name if unit_selection.unit else unit_selection.custom_unit_name,
                            'description': unit_selection.unit.description if unit_selection.unit else unit_selection.custom_unit_description,
                            'priority': unit_selection.priority,
                            'is_custom': unit_selection.is_custom
                        }
                        partner_units.append(unit_info)
                        all_units.append(unit_info)
                    
                    partners_with_units.append({
                        'partner': partner_info,
                        'units': partner_units,
                        'unit_count': len(partner_units)
                    })
                else:
                    # Custom partner with no units selected yet
                    partners_with_units.append({
                        'partner': partner_info,
                        'units': [],
                        'unit_count': 0
                    })
            
            # Calculate onboarding progress
            progress = {
                'native_language_set': user_profile.native_language is not None,
                'industry_set': user_profile.industry_id is not None,
                'role_selected': user_profile.selected_role_id is not None,
                'partners_selected': len(partners) > 0,
                'units_selected': len(all_units) > 0
            }
            
            completion_percentage = sum(progress.values()) / len(progress) * 100
            
            # Build response data
            response_data = {
                'user_profile': {
                    'name': user_profile.user.full_name,
                    'email': user_profile.user.email,
                    'native_language': user_profile.native_language.value if user_profile.native_language else None,
                    'industry': {
                        'id': user_profile.industry_id,
                        'name': user_profile.industry_name
                    } if user_profile.industry_id else None,
                    'role': {
                        'id': user_profile.selected_role_id,
                        'title': user_profile.role_title
                    } if user_profile.selected_role_id else None,
                    'onboarding_status': user_profile.onboarding_status.value
                },
                'communication_partners': partners,
                'partners_with_units': partners_with_units,
                'units_situations': all_units,  # Legacy compatibility
                'total_partners': len(partners),
                'total_units': len(all_units),
                'onboarding_progress': {
                    'steps': progress,
                    'completion_percentage': completion_percentage,
                    'is_complete': completion_percentage == 100
                }
            }
            
            # Cache the response
            self.set_cached_response(cache_key, response_data)
            
            return APIResponse.success(data=response_data)
            
        except Exception as e:
            logger.error(f"Get onboarding summary error: {str(e)}")
            return APIResponse.error(
                message="Failed to get onboarding summary",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OnboardingProgressView(AuthenticatedView, VersionedView):
    """
    Get onboarding progress endpoint.
    Returns current onboarding step and completion status.
    """
    
    def get(self, request):
        """Get onboarding progress."""
        try:
            auth0_id = self.get_auth0_user_id()
            
            # Get user profile
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(auth0_id)
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determine current step and progress
            steps = {
                'native_language': user_profile.native_language is not None,
                'industry': user_profile.industry_id is not None,
                'role': user_profile.selected_role_id is not None,
                'communication_partners': False,  # Will check below
                'communication_units': False     # Will check below
            }
            
            # Check communication selections
            communication_manager = CommunicationManager()
            user_partners = communication_manager.get_user_partners(user_profile.user.id)
            
            if user_partners:
                steps['communication_partners'] = True
                
                # Check if any partner has units selected
                for partner_selection in user_partners:
                    if partner_selection.partner:
                        unit_selections = communication_manager.get_user_units(
                            user_profile.user.id, 
                            partner_selection.partner.id
                        )
                        if unit_selections:
                            steps['communication_units'] = True
                            break
            
            # Find current step
            current_step = None
            for step, completed in steps.items():
                if not completed:
                    current_step = step
                    break
            
            if current_step is None:
                current_step = 'completed'
            
            completed_steps = sum(steps.values())
            total_steps = len(steps)
            completion_percentage = (completed_steps / total_steps) * 100
            
            return APIResponse.success(
                data={
                    'current_step': current_step,
                    'steps': steps,
                    'completed_steps': completed_steps,
                    'total_steps': total_steps,
                    'completion_percentage': completion_percentage,
                    'is_complete': current_step == 'completed',
                    'onboarding_status': user_profile.onboarding_status.value
                }
            )
            
        except Exception as e:
            logger.error(f"Get onboarding progress error: {str(e)}")
            return APIResponse.error(
                message="Failed to get onboarding progress",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )