"""
Base view classes for common functionality across the application.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pydantic import ValidationError

from core.exceptions import (
    ValidationError as DomainValidationError,
    AuthenticationError,
    ConflictError,
    BusinessLogicError
)


class BaseAPIView(APIView):
    """Base view with common error handling and use case execution."""
    
    async def handle_use_case(self, use_case, request_data=None):
        """Execute use case with standard error handling."""
        try:
            if request_data is not None:
                response = await use_case.execute(request_data)
            else:
                response = await use_case.execute()
            
            return Response(
                response.dict(),
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"errors": e.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DomainValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AuthenticationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except ConflictError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        except BusinessLogicError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_use_case_sync(self, use_case, request_data=None):
        """Execute use case synchronously with standard error handling."""
        try:
            if request_data is not None:
                response = use_case.execute(request_data)
            else:
                response = use_case.execute()
            
            return Response(
                response.dict() if hasattr(response, 'dict') else response,
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response(
                {"errors": e.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DomainValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AuthenticationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except ConflictError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        except BusinessLogicError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )