from rest_framework.response import Response
from rest_framework import status
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(
        data: Any,
        message: str = None,
        status_code: int = status.HTTP_200_OK,
        meta: Dict[str, Any] = None
    ) -> Response:
        """Create success response"""
        response_data = {
            "data": data,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "v1",
                **(meta or {})
            }
        }
        
        if message:
            response_data["message"] = message
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        details: List[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: str = None
    ) -> Response:
        """Create error response"""
        return Response({
            "error": {
                "code": code,
                "message": message,
                "details": details or []
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id or str(uuid.uuid4())
            }
        }, status=status_code)
    
    @staticmethod
    def validation_error(errors: List[Dict[str, Any]]) -> Response:
        """Create validation error response"""
        return APIResponse.error(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )