"""
Language selection views for FluentPro v1.
Handles native language selection during onboarding.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError
from authentication.business.user_manager import UserManager
from authentication.models.user import NativeLanguage

logger = logging.getLogger(__name__)


class SetNativeLanguageView(AuthenticatedView, VersionedView):
    """
    Set user's native language endpoint.
    Phase 1 onboarding step.
    """
    
    def post(self, request):
        """Set user's native language."""
        try:
            native_language = request.data.get('native_language')
            
            if not native_language:
                raise ValidationError("native_language is required")
            
            # Validate language against enum
            try:
                language_enum = NativeLanguage(native_language)
            except ValueError:
                valid_languages = [lang.value for lang in NativeLanguage]
                raise ValidationError(
                    f"native_language must be one of: {', '.join(valid_languages)}"
                )
            
            # Update user's native language
            auth0_id = self.get_auth0_user_id()
            user_manager = UserManager()
            
            result = user_manager.update_native_language(auth0_id, native_language)
            
            return APIResponse.success(
                data={
                    'message': 'Native language updated successfully',
                    'native_language': native_language,
                    'user_id': result.get('user_id')
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Native language update error: {str(e)}")
            return APIResponse.error(
                message="Failed to update native language",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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