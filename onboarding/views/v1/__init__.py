"""
Version 1 API views for onboarding module.
"""

from .language_views import SetNativeLanguageView, GetAvailableLanguagesView
from .industry_views import SetIndustryView, GetAvailableIndustriesView
from .communication_views import (
    GetCommunicationPartnersView,
    SelectCommunicationPartnersView,
    GetUserCommunicationPartnersView,
    GetUnitsForPartnerView,
    SelectUnitsForPartnerView,
    GetUserUnitsForPartnerView
)
from .summary_views import GetOnboardingSummaryView

__all__ = [
    'SetNativeLanguageView',
    'GetAvailableLanguagesView',
    'SetIndustryView', 
    'GetAvailableIndustriesView',
    'GetCommunicationPartnersView',
    'SelectCommunicationPartnersView',
    'GetUserCommunicationPartnersView',
    'GetUnitsForPartnerView',
    'SelectUnitsForPartnerView',
    'GetUserUnitsForPartnerView',
    'GetOnboardingSummaryView'
]