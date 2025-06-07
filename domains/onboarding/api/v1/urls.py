from django.urls import path, include

urlpatterns = [
    path('communication/', include('domains.onboarding.api.v1.communication_views')),
    path('industry/', include('domains.onboarding.api.v1.industry_views')),
    path('language/', include('domains.onboarding.api.v1.language_views')),
    path('summary/', include('domains.onboarding.api.v1.summary_views')),
]