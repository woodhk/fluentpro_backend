from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    SignUpView as SignupView,
    RefreshTokenView,
    # UserProfileView,  # TODO: Create this view
    # ChangePasswordView  # TODO: Create this view
)

app_name = 'authentication'

urlpatterns = [
    # Session management
    path('sessions/login/', LoginView.as_view(), name='login'),
    path('sessions/logout/', LogoutView.as_view(), name='logout'),
    path('sessions/refresh/', RefreshTokenView.as_view(), name='refresh-token'),
    
    # User management
    path('users/signup/', SignupView.as_view(), name='signup'),
    # path('users/me/', UserProfileView.as_view(), name='current-user'),  # TODO: Create UserProfileView
    # path('users/me/password/', ChangePasswordView.as_view(), name='change-password'),  # TODO: Create ChangePasswordView
    # path('users/<str:user_id>/', UserProfileView.as_view(), name='user-detail'),  # TODO: Create UserProfileView
]