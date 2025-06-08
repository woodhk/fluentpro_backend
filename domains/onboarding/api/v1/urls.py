from django.urls import path
from .communication_views import SelectCommunicationPartnersView as PartnerSelectionView
from .industry_views import SetIndustryView as IndustrySelectionView, GetAvailableIndustriesView as IndustryListView
from .language_views import SetNativeLanguageView as LanguageSelectionView, GetAvailableLanguagesView as LanguageListView
from .summary_views import GetOnboardingSummaryView as OnboardingSummaryView
# from .views import (
#     OnboardingSessionView,  # TODO: Create this view
#     RoleMatchingView,  # TODO: Create this view
#     RoleListView  # TODO: Create this view
# )

app_name = 'onboarding'

urlpatterns = [
    # Session management
    # path('sessions/', OnboardingSessionView.as_view(), name='session-list'),  # TODO: Create OnboardingSessionView
    # path('sessions/<str:session_id>/', OnboardingSessionView.as_view(), name='session-detail'),  # TODO: Create OnboardingSessionView
    
    # Onboarding steps
    # path('sessions/<str:session_id>/language/', LanguageSelectionView.as_view(), name='select-language'),  # TODO: Update for session-based flow
    # path('sessions/<str:session_id>/industry/', IndustrySelectionView.as_view(), name='select-industry'),  # TODO: Update for session-based flow
    # path('sessions/<str:session_id>/role/', RoleMatchingView.as_view(), name='match-role'),  # TODO: Create RoleMatchingView
    # path('sessions/<str:session_id>/partners/', PartnerSelectionView.as_view(), name='select-partners'),  # TODO: Update for session-based flow
    # path('sessions/<str:session_id>/summary/', OnboardingSummaryView.as_view(), name='session-summary'),  # TODO: Update for session-based flow
    
    # Reference data
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('industries/', IndustryListView.as_view(), name='industry-list'),
    # path('roles/', RoleListView.as_view(), name='role-list'),  # TODO: Create RoleListView
    
    # Temporary: Keep current endpoints for backward compatibility during transition
    path('language/set/', LanguageSelectionView.as_view(), name='set-language-legacy'),
    path('industry/set/', IndustrySelectionView.as_view(), name='set-industry-legacy'),
    path('communication/partners/select/', PartnerSelectionView.as_view(), name='select-partners-legacy'),
    path('summary/', OnboardingSummaryView.as_view(), name='summary-legacy'),
]