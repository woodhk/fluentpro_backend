from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    # Authentication endpoints
    path('auth/', include('domains.authentication.api.v1.urls')),
    
    # Onboarding endpoints
    path('onboarding/', include('domains.onboarding.api.v1.urls')),
    
    # Health check
    path('health/', include('api.common.health')),
    
    # API documentation
    path('docs/', include('api.common.docs')),
]