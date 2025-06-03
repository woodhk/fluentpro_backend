from django.urls import path
from authentication.views.v1 import (
    SignUpView, LoginView, RefreshTokenView, 
    LogoutView, Auth0CallbackView, UserProfileView,
    JobInputView, RoleSelectionView, NewRoleCreationView
)
from authentication.health import HealthCheckView

app_name = 'authentication'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('auth0/callback/', Auth0CallbackView.as_view(), name='auth0_callback'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('job-input/', JobInputView.as_view(), name='job_input'),
    path('role-selection/', RoleSelectionView.as_view(), name='role_selection'),
    path('new-role/', NewRoleCreationView.as_view(), name='new_role_creation'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
]