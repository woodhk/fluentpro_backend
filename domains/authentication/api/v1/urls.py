from django.urls import path, include
from .views import LoginView, SignUpView, LogoutView, RefreshTokenView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh_token'),
    path('roles/', include('domains.authentication.api.v1.role_views')),
    path('users/', include('domains.authentication.api.v1.user_views')),
]