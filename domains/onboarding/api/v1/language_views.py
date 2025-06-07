"""
Language selection views for FluentPro v1.
Handles native language selection during onboarding.
"""

from rest_framework import status
from rest_framework.response import Response
import logging

from api.common.base_views import BaseAPIView
from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError
from authentication.business.user_manager import UserManager
from authentication.models.user import NativeLanguage
from application.container import container
from domains.onboarding.dto.requests import NativeLanguageRequest

logger = logging.getLogger(__name__)


class SetNativeLanguageView(BaseAPIView, AuthenticatedView, VersionedView):
    """
    Set user's native language endpoint.
    Phase 1 onboarding step.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.select_native_language = container.onboarding_use_cases.select_native_language()
    
    def post(self, request):
        """Set user's native language."""
        # Parse request
        try:
            language_request = NativeLanguageRequest(**request.data)
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
            lambda: self.select_native_language.execute(
                auth0_id, language_request.native_language
            )
        )


class GetAvailableLanguagesView(CachedView, VersionedView):
    """
    Get available native languages endpoint.
    Returns list of supported languages.
    """
    cache_timeout = 3600  # 1 hour cache (rarely changes)
    
    def get(self, request):
        """Get available native languages."""
        try:
            # Check cache first
            cache_key = self.get_cache_key("languages")
            cached_languages = self.get_cached_response(cache_key)
            
            if cached_languages:
                return APIResponse.success(data=cached_languages)
            
            # Build language options from enum
            languages = []
            for lang in NativeLanguage:
                languages.append({
                    'value': lang.value,
                    'label': lang.value.replace('_', ' ').title()
                })
            
            response_data = {'languages': languages}
            
            # Cache the response
            self.set_cached_response(cache_key, response_data)
            
            return APIResponse.success(data=response_data)
            
        except Exception as e:
            logger.error(f"Get available languages error: {str(e)}")
            return APIResponse.error(
                message="Failed to get available languages",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )