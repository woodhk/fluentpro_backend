"""
Standardized API response helpers for consistent response formatting across the application.
"""

from rest_framework import status
from rest_framework.response import Response
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Utility class for creating standardized API responses.
    Ensures consistent response format across all endpoints.
    """
    
    @staticmethod
    def success(
        data: Any = None, 
        message: Optional[str] = None, 
        status_code: int = status.HTTP_200_OK,
        **kwargs
    ) -> Response:
        """
        Create a standardized success response.
        
        Args:
            data: Response data (can be dict, list, string, etc.)
            message: Optional success message
            status_code: HTTP status code (default: 200)
            **kwargs: Additional fields to include in response
            
        Returns:
            Response: DRF Response object with standardized format
        """
        response_data = {
            'success': True
        }
        
        if message:
            response_data['message'] = message
            
        if data is not None:
            # If data is a dict, merge it directly for backward compatibility
            if isinstance(data, dict) and not message:
                response_data.update(data)
            else:
                response_data['data'] = data
        
        # Add any additional fields
        response_data.update(kwargs)
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str,
        details: Optional[Union[Dict, str]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None
    ) -> Response:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            details: Additional error details (validation errors, etc.)
            status_code: HTTP status code (default: 400)
            error_code: Optional error code for client handling
            
        Returns:
            Response: DRF Response object with standardized error format
        """
        response_data = {
            'success': False,
            'error': message
        }
        
        if details:
            response_data['details'] = details
            
        if error_code:
            response_data['error_code'] = error_code
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors: Dict[str, Any]) -> Response:
        """
        Create a standardized validation error response.
        
        Args:
            errors: Validation errors from serializer
            
        Returns:
            Response: DRF Response object with validation error format
        """
        return APIResponse.error(
            message="Validation failed",
            details=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR"
        )
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> Response:
        """
        Create a standardized 404 error response.
        
        Args:
            message: Error message
            
        Returns:
            Response: DRF Response object with 404 error
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Response:
        """
        Create a standardized 401 error response.
        
        Args:
            message: Error message
            
        Returns:
            Response: DRF Response object with 401 error
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> Response:
        """
        Create a standardized 403 error response.
        
        Args:
            message: Error message
            
        Returns:
            Response: DRF Response object with 403 error
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        log_message: Optional[str] = None
    ) -> Response:
        """
        Create a standardized 500 error response with logging.
        
        Args:
            message: Public error message
            log_message: Detailed message for logging (not exposed to client)
            
        Returns:
            Response: DRF Response object with 500 error
        """
        if log_message:
            logger.error(f"Internal server error: {log_message}")
        
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR"
        )
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
        **kwargs
    ) -> Response:
        """
        Create a standardized 201 created response.
        
        Args:
            data: Created resource data
            message: Success message
            **kwargs: Additional fields
            
        Returns:
            Response: DRF Response object with 201 status
        """
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            **kwargs
        )
    
    @staticmethod
    def accepted(
        data: Any = None,
        message: str = "Request accepted for processing",
        **kwargs
    ) -> Response:
        """
        Create a standardized 202 accepted response.
        
        Args:
            data: Response data
            message: Success message
            **kwargs: Additional fields
            
        Returns:
            Response: DRF Response object with 202 status
        """
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_202_ACCEPTED,
            **kwargs
        )


class ServiceResponse:
    """
    Utility class for service layer responses.
    Used for consistent response format between service methods.
    """
    
    @staticmethod
    def success(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a successful service response.
        
        Args:
            data: Response data
            message: Optional message
            
        Returns:
            Dict: Service response dictionary
        """
        response = {'success': True}
        
        if data is not None:
            response['data'] = data
            
        if message:
            response['message'] = message
            
        return response
    
    @staticmethod
    def error(message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an error service response.
        
        Args:
            message: Error message
            error_code: Optional error code
            
        Returns:
            Dict: Service response dictionary
        """
        response = {
            'success': False,
            'error': message
        }
        
        if error_code:
            response['error_code'] = error_code
            
        return response