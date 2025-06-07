"""Onboarding domain events."""

from .session_events import (
    OnboardingSessionStartedEvent,
    OnboardingStepCompletedEvent,
    OnboardingStepSkippedEvent,
    OnboardingSessionPausedEvent,
    OnboardingSessionResumedEvent,
    OnboardingSessionCompletedEvent,
    OnboardingSessionAbandonedEvent,
    OnboardingSessionExpiredEvent
)

from .preference_events import (
    LanguageSelectedEvent,
    IndustrySelectedEvent,
    RoleSelectedEvent,
    CustomRoleCreatedEvent,
    RoleMatchPerformedEvent,
    CommunicationPartnersSelectedEvent,
    PartnerSituationsConfiguredEvent,
    LearningGoalsDefinedEvent,
    PersonalizationCompleteEvent
)

from . import handlers

__all__ = [
    # Session Events
    'OnboardingSessionStartedEvent',
    'OnboardingStepCompletedEvent',
    'OnboardingStepSkippedEvent',
    'OnboardingSessionPausedEvent',
    'OnboardingSessionResumedEvent',
    'OnboardingSessionCompletedEvent',
    'OnboardingSessionAbandonedEvent',
    'OnboardingSessionExpiredEvent',
    # Preference Events
    'LanguageSelectedEvent',
    'IndustrySelectedEvent',
    'RoleSelectedEvent',
    'CustomRoleCreatedEvent',
    'RoleMatchPerformedEvent',
    'CommunicationPartnersSelectedEvent',
    'PartnerSituationsConfiguredEvent',
    'LearningGoalsDefinedEvent',
    'PersonalizationCompleteEvent',
    # Handlers
    'handlers',
]