"""Authentication domain events."""

from .user_events import (
    UserRegisteredEvent,
    UserLoggedInEvent,
    UserLoggedOutEvent,
    UserProfileUpdatedEvent,
    UserPasswordChangedEvent,
    UserPasswordResetRequestedEvent,
    UserPasswordResetCompletedEvent,
    UserAccountActivatedEvent,
    UserAccountDeactivatedEvent,
    UserEmailVerifiedEvent,
    UserRoleAssignedEvent,
    UserRoleRevokedEvent
)

from .session_events import (
    SessionCreatedEvent,
    SessionExpiredEvent,
    SessionRefreshedEvent,
    LoginAttemptFailedEvent,
    AccountLockedEvent,
    AccountUnlockedEvent,
    SuspiciousActivityDetectedEvent,
    TwoFactorEnabledEvent,
    TwoFactorDisabledEvent,
    PermissionGrantedEvent,
    PermissionRevokedEvent
)

from . import handlers

__all__ = [
    # User Events
    'UserRegisteredEvent',
    'UserLoggedInEvent',
    'UserLoggedOutEvent',
    'UserProfileUpdatedEvent',
    'UserPasswordChangedEvent',
    'UserPasswordResetRequestedEvent',
    'UserPasswordResetCompletedEvent',
    'UserAccountActivatedEvent',
    'UserAccountDeactivatedEvent',
    'UserEmailVerifiedEvent',
    'UserRoleAssignedEvent',
    'UserRoleRevokedEvent',
    # Session Events
    'SessionCreatedEvent',
    'SessionExpiredEvent',
    'SessionRefreshedEvent',
    'LoginAttemptFailedEvent',
    'AccountLockedEvent',
    'AccountUnlockedEvent',
    'SuspiciousActivityDetectedEvent',
    'TwoFactorEnabledEvent',
    'TwoFactorDisabledEvent',
    'PermissionGrantedEvent',
    'PermissionRevokedEvent',
    # Handlers
    'handlers',
]