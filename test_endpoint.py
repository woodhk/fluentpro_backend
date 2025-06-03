"""
Simple test endpoint to check if views are working.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    """Simple health check endpoint."""
    
    def get(self, request):
        logger.info("Health check endpoint called")
        return Response({
            'status': 'ok',
            'message': 'Server is running'
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        logger.info("Health check POST endpoint called")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Test basic imports
            from authentication.business.user_manager import UserManager
            from authentication.business.role_manager import RoleManager
            
            logger.info("Imports successful")
            
            return Response({
                'status': 'ok',
                'message': 'POST endpoint working',
                'imports': 'successful',
                'data_received': request.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)