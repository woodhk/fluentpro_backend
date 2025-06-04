"""
API v1 URL configuration.
Organizes all v1 API endpoints with clear namespacing.
"""

from django.urls import path, include

# Import v1 views
from authentication.views.v1 import (
    SignUpView, LoginView, RefreshTokenView, LogoutView, Auth0CallbackView,
    UserProfileView, JobInputView, RoleSelectionView, NewRoleCreationView
)
from authentication.health import HealthCheckView
from onboarding.views.v1 import (
    SetNativeLanguageView, GetAvailableLanguagesView,
    SetIndustryView, GetAvailableIndustriesView,
    GetCommunicationPartnersView, SelectCommunicationPartnersView,
    GetUserCommunicationPartnersView, GetUnitsForPartnerView,
    SelectUnitsForPartnerView, GetUserUnitsForPartnerView,
    GetOnboardingSummaryView
)

app_name = 'v1'

# Authentication endpoints
auth_patterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('callback/', Auth0CallbackView.as_view(), name='auth0_callback'),
]

# User management endpoints
user_patterns = [
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]

# Role management endpoints
role_patterns = [
    path('job-input/', JobInputView.as_view(), name='job_input'),
    path('role-selection/', RoleSelectionView.as_view(), name='role_selection'),
    path('new-role/', NewRoleCreationView.as_view(), name='new_role_creation'),
]

# Onboarding endpoints
onboarding_patterns = [
    # Language selection
    path('set-language/', SetNativeLanguageView.as_view(), name='set_native_language'),
    path('languages/', GetAvailableLanguagesView.as_view(), name='get_available_languages'),
    
    # Industry selection  
    path('set-industry/', SetIndustryView.as_view(), name='set_industry'),
    path('industries/', GetAvailableIndustriesView.as_view(), name='get_available_industries'),
    
    # Communication partners
    path('communication-partners/', GetCommunicationPartnersView.as_view(), name='get_communication_partners'),
    path('select-partners/', SelectCommunicationPartnersView.as_view(), name='select_communication_partners'),
    path('user-partners/', GetUserCommunicationPartnersView.as_view(), name='get_user_communication_partners'),
    
    # Communication units
    path('partner/<str:partner_id>/units/', GetUnitsForPartnerView.as_view(), name='get_units_for_partner'),
    path('partner/<str:partner_id>/select-units/', SelectUnitsForPartnerView.as_view(), name='select_units_for_partner'),
    path('partner/<str:partner_id>/user-units/', GetUserUnitsForPartnerView.as_view(), name='get_user_units_for_partner'),
    
    # Summary
    path('summary/', GetOnboardingSummaryView.as_view(), name='get_onboarding_summary'),
]

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health_check'),
    
    # Authentication
    path('auth/', include(auth_patterns)),
    
    # User management
    path('user/', include(user_patterns)),
    
    # Role management
    path('roles/', include(role_patterns)),
    
    # Onboarding
    path('onboarding/', include(onboarding_patterns)),
]