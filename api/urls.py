from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('v1/', include('api.v1.urls', namespace='v1')),
    path('v2/', include('api.v2.urls', namespace='v2')),
    # Default to latest stable version
    path('', include('api.v1.urls')),
]