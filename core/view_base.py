"""
Base view classes for FluentPro API.
Provides reusable mixins and base classes for consistent view behavior.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from typing import Optional, Dict, Any
import logging

from core.responses import APIResponse
from core.services import ServiceMixin
from core.exceptions import (
    SupabaseUserNotFoundError,
    ValidationError,
    AuthenticationError,
    BusinessLogicError
)

logger = logging.getLogger(__name__)


class BaseFluentProView(APIView, ServiceMixin):
    """
    Base view class for all FluentPro API endpoints.
    Provides common functionality and standardized error handling.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add common request processing."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except SupabaseUserNotFoundError as e:
            return APIResponse.error(
                message="User not found",
                details=str(e),
                status=status.HTTP_404_NOT_FOUND
            )
        except AuthenticationError as e:
            return APIResponse.error(
                message="Authentication failed",
                details=str(e),
                status=status.HTTP_401_UNAUTHORIZED
            )
        except ValidationError as e:
            return APIResponse.error(
                message="Validation failed",
                details=str(e),
                status=status.HTTP_400_BAD_REQUEST
            )
        except BusinessLogicError as e:
            return APIResponse.error(
                message="Business logic error",
                details=str(e),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}: {str(e)}")
            return APIResponse.error(
                message="Internal server error",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuthenticatedView(BaseFluentProView):
    """
    Base class for authenticated API endpoints.
    Requires valid JWT authentication.
    """
    permission_classes = [IsAuthenticated]
    
    def get_auth0_user_id(self) -> str:
        """Get Auth0 user ID from JWT token."""
        return self.request.user.sub
    
    def get_user_email(self) -> str:
        """Get user email from JWT token."""
        return self.request.user.email
    
    def get_current_user(self):
        """Get current user from repository."""
        auth0_id = self.get_auth0_user_id()
        return self.services.users.get_by_auth0_id(auth0_id)
    
    def get_user_or_404(self):
        """Get current user or raise 404 if not found."""
        user = self.get_current_user()
        if not user:
            raise SupabaseUserNotFoundError(self.get_auth0_user_id())
        return user


class PublicView(BaseFluentProView):
    """
    Base class for public API endpoints.
    Does not require authentication.
    """
    permission_classes = [AllowAny]


@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptView(BaseFluentProView):
    """
    Base class for views that need CSRF exemption.
    Typically used for POST endpoints from mobile apps.
    """
    pass


class VersionedView(BaseFluentProView):
    """
    Base class for versioned API endpoints.
    Supports API versioning through headers or URL parameters.
    """
    supported_versions = ['1.0']
    default_version = '1.0'
    
    def get_api_version(self) -> str:
        """
        Get API version from request headers or URL parameters.
        Returns default version if not specified.
        """
        # Check header first
        version = self.request.META.get('HTTP_API_VERSION')
        
        # Check URL parameter as fallback
        if not version:
            version = self.request.GET.get('version')
        
        # Use default if not specified or invalid
        if not version or version not in self.supported_versions:
            version = self.default_version
        
        return version
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to check API version."""
        self.api_version = self.get_api_version()
        return super().dispatch(request, *args, **kwargs)


class PaginatedView(AuthenticatedView):
    """
    Base class for paginated endpoints.
    Provides common pagination logic.
    """
    default_page_size = 20
    max_page_size = 100
    
    def get_pagination_params(self) -> Dict[str, int]:
        """Get pagination parameters from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            page_size = int(self.request.GET.get('page_size', self.default_page_size))
            
            # Validate parameters
            page = max(1, page)
            page_size = min(max(1, page_size), self.max_page_size)
            
            offset = (page - 1) * page_size
            
            return {
                'page': page,
                'page_size': page_size,
                'offset': offset,
                'limit': page_size
            }
        except (ValueError, TypeError):
            return {
                'page': 1,
                'page_size': self.default_page_size,
                'offset': 0,
                'limit': self.default_page_size
            }
    
    def paginated_response(self, data: list, total_count: int, **kwargs) -> Response:
        """Create paginated response."""
        pagination = self.get_pagination_params()
        
        has_next = (pagination['offset'] + pagination['page_size']) < total_count
        has_previous = pagination['page'] > 1
        
        response_data = {
            'results': data,
            'pagination': {
                'page': pagination['page'],
                'page_size': pagination['page_size'],
                'total_count': total_count,
                'total_pages': (total_count + pagination['page_size'] - 1) // pagination['page_size'],
                'has_next': has_next,
                'has_previous': has_previous
            }
        }
        
        # Add any additional data
        response_data.update(kwargs)
        
        return APIResponse.success(data=response_data)


class CachedView(AuthenticatedView):
    """
    Base class for views with caching support.
    Provides cache key generation and cache control.
    """
    cache_timeout = 300  # 5 minutes default
    cache_key_prefix = 'fluentpro'
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key for this view."""
        user_id = self.get_auth0_user_id()
        view_name = self.__class__.__name__.lower()
        
        # Include any additional parameters
        params = '_'.join([str(arg) for arg in args])
        if params:
            return f"{self.cache_key_prefix}:{view_name}:{user_id}:{params}"
        else:
            return f"{self.cache_key_prefix}:{view_name}:{user_id}"
    
    def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available."""
        try:
            # Implementation depends on cache backend (Redis, etc.)
            # For now, return None (no cache)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
            return None
    
    def set_cached_response(self, cache_key: str, data: Any) -> None:
        """Cache response data."""
        try:
            # Implementation depends on cache backend (Redis, etc.)
            # For now, do nothing
            pass
        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")


class HealthCheckView(PublicView):
    """
    Health check endpoint for monitoring.
    """
    
    def get(self, request):
        """Simple health check."""
        return APIResponse.success(
            data={
                'status': 'healthy',
                'service': 'fluentpro-backend',
                'version': '1.0.0'
            }
        )