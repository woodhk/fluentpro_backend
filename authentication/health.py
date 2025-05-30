from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.conf import settings
import os


class HealthCheckView(APIView):
    """
    Health check endpoint for deployment monitoring
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Simple health check that returns system status
        """
        health_data = {
            'status': 'healthy',
            'service': 'fluentpro-backend',
            'version': '1.0.0',
            'environment': 'production' if not settings.DEBUG else 'development',
            'auth0_configured': bool(getattr(settings, 'AUTH0_DOMAIN', None)),
            'supabase_configured': bool(getattr(settings, 'SUPABASE_URL', None))
        }
        
        return Response(health_data, status=status.HTTP_200_OK)