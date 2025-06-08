"""
Industry selection views for FluentPro v1.
Handles industry selection during onboarding.
"""

from rest_framework import status
from rest_framework.response import Response
from datetime import timedelta
import logging

from api.common.base_views import BaseAPIView
from api.common.responses import APIResponse
from api.common.documentation import document_endpoint
from authentication.backends import Auth0JWTAuthentication
from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.exceptions import ValidationError
from authentication.business.user_manager import UserManager
from application.container import container
from domains.onboarding.dto.requests import UserIndustryRequest
from application.decorators import validate_input, audit_log, cache

logger = logging.getLogger(__name__)


class SetIndustryView(BaseAPIView, AuthenticatedView, VersionedView):
    """
    Set user's industry endpoint.
    Phase 1 onboarding step.
    """
    authentication_classes = [Auth0JWTAuthentication]
    
    @document_endpoint(
        summary="Set User Industry",
        description="Set user's industry during onboarding",
        request_examples=[{
            "name": "Valid Industry Selection",
            "value": {
                "industry_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }]
    )
    @validate_input(UserIndustryRequest)
    @audit_log(action="set_industry", resource_type="onboarding")
    def post(self, request, **validated_data):
        """Set user's industry."""
        industry_request = UserIndustryRequest(**validated_data)
        
        # Get user auth0_id
        try:
            auth0_id = self.get_auth0_user_id()
        except Exception as e:
            return APIResponse.error(
                message="Authentication required",
                code="AUTH_REQUIRED",
                status_code=status.HTTP_401_UNAUTHORIZED
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
    
    @document_endpoint(
        summary="Get Available Industries",
        description="Retrieve list of selectable industries"
    )
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
                code="INDUSTRIES_FETCH_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )