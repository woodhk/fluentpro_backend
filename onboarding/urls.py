from django.urls import path
from . import views

urlpatterns = [
    # Phase 1 endpoints
    path('phase1/set-native-language/', views.set_native_language, name='set_native_language'),
    path('phase1/available-languages/', views.get_available_languages, name='get_available_languages'),
    path('phase1/set-industry/', views.set_industry, name='set_industry'),
    path('phase1/available-industries/', views.get_available_industries, name='get_available_industries'),
    
    # Phase 2 endpoints - Structured Communication Needs Collection
    path('phase2/communication-partners/', views.get_communication_partners, name='get_communication_partners'),
    path('phase2/select-communication-partners/', views.select_communication_partners, name='select_communication_partners'),
    path('phase2/user-communication-partners/', views.get_user_communication_partners, name='get_user_communication_partners'),
    path('phase2/units/<str:partner_id>/', views.get_units_for_partner, name='get_units_for_partner'),
    path('phase2/select-units/<str:partner_id>/', views.select_units_for_partner, name='select_units_for_partner'),
    path('phase2/user-units/<str:partner_id>/', views.get_user_units_for_partner, name='get_user_units_for_partner'),
    
    # Summary endpoint
    path('summary/', views.get_onboarding_summary, name='get_onboarding_summary'),
]