from django.urls import path
from onboarding.views.v1 import (
    SetNativeLanguageView, GetAvailableLanguagesView,
    SetIndustryView, GetAvailableIndustriesView,
    GetCommunicationPartnersView, SelectCommunicationPartnersView,
    GetUserCommunicationPartnersView, GetUnitsForPartnerView,
    SelectUnitsForPartnerView, GetUserUnitsForPartnerView,
    GetOnboardingSummaryView
)

app_name = 'onboarding'

urlpatterns = [
    # Phase 1 endpoints
    path('phase1/set-native-language/', SetNativeLanguageView.as_view(), name='set_native_language'),
    path('phase1/available-languages/', GetAvailableLanguagesView.as_view(), name='get_available_languages'),
    path('phase1/set-industry/', SetIndustryView.as_view(), name='set_industry'),
    path('phase1/available-industries/', GetAvailableIndustriesView.as_view(), name='get_available_industries'),
    
    # Phase 2 endpoints - Structured Communication Needs Collection
    path('phase2/communication-partners/', GetCommunicationPartnersView.as_view(), name='get_communication_partners'),
    path('phase2/select-communication-partners/', SelectCommunicationPartnersView.as_view(), name='select_communication_partners'),
    path('phase2/user-communication-partners/', GetUserCommunicationPartnersView.as_view(), name='get_user_communication_partners'),
    path('phase2/units/<str:partner_id>/', GetUnitsForPartnerView.as_view(), name='get_units_for_partner'),
    path('phase2/select-units/<str:partner_id>/', SelectUnitsForPartnerView.as_view(), name='select_units_for_partner'),
    path('phase2/user-units/<str:partner_id>/', GetUserUnitsForPartnerView.as_view(), name='get_user_units_for_partner'),
    
    # Summary endpoint
    path('summary/', GetOnboardingSummaryView.as_view(), name='get_onboarding_summary'),
]