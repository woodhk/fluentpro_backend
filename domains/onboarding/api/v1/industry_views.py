"""
Industry selection views for FluentPro v1.
Handles industry selection during onboarding.
"""

from rest_framework import status
from rest_framework.response import Response
import logging

from api.common.base_views import BaseAPIView
from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError
from authentication.business.user_manager import UserManager
from application.container import container
from domains.onboarding.dto.requests import UserIndustryRequest

logger = logging.getLogger(__name__)


class SetIndustryView(BaseAPIView, AuthenticatedView, VersionedView):
    """
    Set user's industry endpoint.
    Phase 1 onboarding step.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.select_user_industry = container.onboarding_use_cases.select_user_industry()
    
    def post(self, request):
        """Set user's industry."""
        # Parse request
        try:
            industry_request = UserIndustryRequest(**request.data)
        except Exception as e:
            return Response(
                {"errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user auth0_id
        try:
            auth0_id = self.get_auth0_user_id()
        except Exception as e:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Execute use case
        return self.handle_use_case_sync(
            lambda: self.select_user_industry.execute(
                auth0_id, 
                industry_request.industry_id, 
                industry_request.industry_name
            )
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