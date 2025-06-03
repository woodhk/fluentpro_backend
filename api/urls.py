"""
API URL configuration with versioning support.
Routes API requests to appropriate version handlers.
"""

from django.urls import path, include
from core.view_base import HealthCheckView

app_name = 'api'

urlpatterns = [
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health_check'),
    
    # API version 1
    path('v1/', include('api.v1.urls', namespace='v1')),
]