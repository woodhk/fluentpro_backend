"""
Mixins for common view functionality across the FluentPro Backend application.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from typing import Optional, Dict, Any
import logging

from .responses import APIResponse
from .exceptions import (
    AuthenticationError, 
    SupabaseUserNotFoundError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)


class AuthenticatedViewMixin:
    """
    Mixin that provides common authentication-related functionality.
    """
    permission_classes = [IsAuthenticated]
    
    def get_auth0_user_id(self) -> str:
        """
        Get the Auth0 user ID from the authenticated request.
        
        Returns:
            str: Auth0 user ID
            
        Raises:
            AuthenticationError: If auth0_id is not found in request
        """
        auth0_id = getattr(self.request.user, 'sub', None)
        if not auth0_id:
            raise AuthenticationError("Invalid authentication: Auth0 ID not found")
        return auth0_id
    
    def get_user_email(self) -> Optional[str]:
        """
        Get the user's email from the authenticated request.
        
        Returns:
            Optional[str]: User's email if available
        """
        return getattr(self.request.user, 'email', None)


class ServiceMixin:
    """
    Mixin that provides lazy initialization of external services.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._supabase_service = None
        self._auth0_service = None
        self._azure_search_service = None
        self._azure_openai_service = None
    
    def get_supabase_service(self):
        """
        Get or create Supabase service instance.
        
        Returns:
            SupabaseService: Supabase service instance
        """
        if self._supabase_service is None:
            try:
                from authentication.services.supabase_service import SupabaseService
                self._supabase_service = SupabaseService()
            except Exception as e:
                logger.error(f"Failed to initialize Supabase service: {str(e)}")
                raise ServiceUnavailableError("Supabase")
        return self._supabase_service
    
    def get_auth0_service(self):
        """
        Get or create Auth0 service instance.
        
        Returns:
            Auth0Service: Auth0 service instance
        """
        if self._auth0_service is None:
            try:
                from authentication.services.auth0_service import Auth0Service
                self._auth0_service = Auth0Service()
            except Exception as e:
                logger.error(f"Failed to initialize Auth0 service: {str(e)}")
                raise ServiceUnavailableError("Auth0")
        return self._auth0_service
    
    def get_azure_search_service(self):
        """
        Get or create Azure Search service instance.
        
        Returns:
            AzureSearchService: Azure Search service instance
        """
        if self._azure_search_service is None:
            try:
                from authentication.services.azure_search_service import AzureSearchService
                self._azure_search_service = AzureSearchService()
            except Exception as e:
                logger.error(f"Failed to initialize Azure Search service: {str(e)}")
                raise ServiceUnavailableError("Azure Search")
        return self._azure_search_service
    
    def get_azure_openai_service(self):
        """
        Get or create Azure OpenAI service instance.
        
        Returns:
            AzureOpenAIService: Azure OpenAI service instance
        """
        if self._azure_openai_service is None:
            try:
                from authentication.services.azure_openai_service import AzureOpenAIService
                self._azure_openai_service = AzureOpenAIService()
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI service: {str(e)}")
                raise ServiceUnavailableError("Azure OpenAI")
        return self._azure_openai_service


class ErrorHandlingMixin:
    """
    Mixin that provides standardized error handling for views.
    """
    
    def handle_exception(self, exc):
        """
        Handle exceptions and return standardized error responses.
        
        Args:
            exc: The exception that was raised
            
        Returns:
            Response: Standardized error response
        """
        from .exceptions import FluentProException
        
        if isinstance(exc, FluentProException):
            return APIResponse.error(
                message=exc.message,
                details=exc.details if exc.details else None,
                status_code=getattr(exc, 'status_code', 400),
                error_code=exc.error_code
            )
        
        # Log unexpected exceptions
        logger.exception(f"Unexpected error in {self.__class__.__name__}: {str(exc)}")
        
        # Return generic error for unexpected exceptions
        return APIResponse.internal_error(
            message="An unexpected error occurred",
            log_message=str(exc)
        )


class UserLookupMixin(AuthenticatedViewMixin, ServiceMixin):
    """
    Mixin that provides user lookup functionality.
    """
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Get the current authenticated user from Supabase.
        
        Returns:
            Dict[str, Any]: User data from Supabase
            
        Raises:
            SupabaseUserNotFoundError: If user is not found in Supabase
        """
        auth0_id = self.get_auth0_user_id()
        supabase_service = self.get_supabase_service()
        
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        if not user:
            raise SupabaseUserNotFoundError(auth0_id)
        
        return user
    
    def get_user_full_profile(self) -> Dict[str, Any]:
        """
        Get the current user's full profile including related data.
        
        Returns:
            Dict[str, Any]: User profile with industry and role information
            
        Raises:
            SupabaseUserNotFoundError: If user is not found in Supabase
        """
        auth0_id = self.get_auth0_user_id()
        supabase_service = self.get_supabase_service()
        
        user_profile = supabase_service.get_user_full_profile(auth0_id)
        if not user_profile:
            raise SupabaseUserNotFoundError(auth0_id)
        
        return user_profile


class BaseFluentProView(
    APIView, 
    AuthenticatedViewMixin, 
    ServiceMixin, 
    ErrorHandlingMixin,
    UserLookupMixin
):
    """
    Base view class that combines all common mixins.
    Use this as the base class for most authenticated API views.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle exceptions consistently.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            return self.handle_exception(exc)


class PublicBaseView(APIView, ServiceMixin, ErrorHandlingMixin):
    """
    Base view class for public (non-authenticated) endpoints.
    """
    permission_classes = []
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to handle exceptions consistently.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            return self.handle_exception(exc)