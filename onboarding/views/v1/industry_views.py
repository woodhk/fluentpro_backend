"""
Industry selection views for FluentPro v1.
Handles industry selection during onboarding.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class SetIndustryView(AuthenticatedView, VersionedView):
    """
    Set user's industry endpoint.
    Phase 1 onboarding step.
    """
    
    def post(self, request):
        """Set user's industry."""
        try:
            industry_id = request.data.get('industry_id')
            
            if not industry_id:
                raise ValidationError("industry_id is required")
            
            # Update user's industry
            auth0_id = self.get_auth0_user_id()
            user_manager = UserManager()
            
            result = user_manager.update_industry(auth0_id, industry_id)
            
            return APIResponse.success(
                data={
                    'message': 'Industry updated successfully',
                    'industry_id': industry_id,
                    'industry_name': result.get('industry_name'),
                    'user_id': result.get('user_id')
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Industry update error: {str(e)}")
            return APIResponse.error(
                message="Failed to update industry",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetAvailableIndustriesView(CachedView, VersionedView):
    """
    Get available industries endpoint.
    Returns list of selectable industries.
    """
    cache_timeout = 1800  # 30 minutes cache
    
    def get(self, request):
        """Get available industries."""
        try:
            # Check cache first
            cache_key = self.get_cache_key("industries")
            cached_industries = self.get_cached_response(cache_key)
            
            if cached_industries:
                return APIResponse.success(data=cached_industries)
            
            # Get industries using user manager
            user_manager = UserManager()
            industries = user_manager.get_available_industries()
            
            response_data = {'industries': industries}
            
            # Cache the response
            self.set_cached_response(cache_key, response_data)
            
            return APIResponse.success(data=response_data)
            
        except Exception as e:
            logger.error(f"Get available industries error: {str(e)}")
            return APIResponse.error(
                message="Failed to get available industries",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )