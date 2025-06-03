"""
Version 1 API views for authentication module.
"""

from .auth_views import SignUpView, LoginView, RefreshTokenView, LogoutView, Auth0CallbackView
from .user_views import UserProfileView
from .role_views import JobInputView, RoleSelectionView, NewRoleCreationView

__all__ = [
    'SignUpView',
    'LoginView', 
    'RefreshTokenView',
    'LogoutView',
    'Auth0CallbackView',
    'UserProfileView',
    'JobInputView',
    'RoleSelectionView',
    'NewRoleCreationView'
]