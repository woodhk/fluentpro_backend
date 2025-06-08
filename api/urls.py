from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

app_name = 'api'

urlpatterns = [
    # API versions
    path('v1/', include('api.v1.urls', namespace='v1')),
    path('v2/', include('api.v2.urls', namespace='v2')),
    
    # Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # Default to latest stable version
    path('', include('api.v1.urls')),
]