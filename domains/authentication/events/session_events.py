"""
Session and authentication-related domain events.
These events track authentication sessions and security-related activities.
"""

from datetime import datetime
from typing import Optional

from domains.shared.events.base_event import DomainEvent


class SessionCreatedEvent(DomainEvent):
    """Event raised when a new authentication session is created."""
    
    user_id: str
    session_id: str
    session_type: str = "web"  # web, mobile, api
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    
    def __init__(self, **data):
        super().__init__(
            event_type="session.created",
            aggregate_id=data.get('session_id'),
            **data
        )


class SessionExpiredEvent(DomainEvent):
    """Event raised when an authentication session expires."""
    
    user_id: str
    session_id: str
    expiry_reason: str = "timeout"  # timeout, manual_invalidation, security_policy
    
    def __init__(self, **data):
        super().__init__(
            event_type="session.expired",
            aggregate_id=data.get('session_id'),
            **data
        )


class SessionRefreshedEvent(DomainEvent):
    """Event raised when an authentication session is refreshed."""
    
    user_id: str
    session_id: str
    old_refresh_token: str
    new_refresh_token: str
    new_expires_at: datetime
    
    def __init__(self, **data):
        super().__init__(
            event_type="session.refreshed",
            aggregate_id=data.get('session_id'),
            **data
        )


class LoginAttemptFailedEvent(DomainEvent):
    """Event raised when a login attempt fails."""
    
    email: str
    failure_reason: str  # invalid_credentials, account_locked, account_disabled
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    attempt_count: int = 1
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.login_attempt_failed",
            aggregate_id=data.get('email'),
            **data
        )


class AccountLockedEvent(DomainEvent):
    """Event raised when a user account is locked due to security policies."""
    
    user_id: str
    email: str
    lock_reason: str  # too_many_failed_attempts, suspicious_activity, admin_action
    locked_until: Optional[datetime] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.account_locked",
            aggregate_id=data.get('user_id'),
            **data
        )


class AccountUnlockedEvent(DomainEvent):
    """Event raised when a locked user account is unlocked."""
    
    user_id: str
    email: str
    unlock_method: str  # time_expiry, admin_action, password_reset
    unlocked_by: Optional[str] = None  # admin user_id or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.account_unlocked",
            aggregate_id=data.get('user_id'),
            **data
        )


class SuspiciousActivityDetectedEvent(DomainEvent):
    """Event raised when suspicious authentication activity is detected."""
    
    user_id: Optional[str] = None
    email: Optional[str] = None
    activity_type: str  # unusual_location, rapid_requests, credential_stuffing
    severity: str = "medium"  # low, medium, high, critical
    ip_address: Optional[str] = None
    details: dict = {}
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.suspicious_activity_detected",
            aggregate_id=data.get('user_id') or data.get('email', 'unknown'),
            **data
        )


class TwoFactorEnabledEvent(DomainEvent):
    """Event raised when a user enables two-factor authentication."""
    
    user_id: str
    email: str
    method: str  # sms, app, email
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.two_factor_enabled",
            aggregate_id=data.get('user_id'),
            **data
        )


class TwoFactorDisabledEvent(DomainEvent):
    """Event raised when a user disables two-factor authentication."""
    
    user_id: str
    email: str
    method: str  # sms, app, email
    disabled_by: str = "user"  # user, admin, system
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.two_factor_disabled",
            aggregate_id=data.get('user_id'),
            **data
        )


class PermissionGrantedEvent(DomainEvent):
    """Event raised when a permission is granted to a user."""
    
    user_id: str
    permission: str
    resource: Optional[str] = None
    granted_by: str  # admin user_id or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.permission_granted",
            aggregate_id=data.get('user_id'),
            **data
        )


class PermissionRevokedEvent(DomainEvent):
    """Event raised when a permission is revoked from a user."""
    
    user_id: str
    permission: str
    resource: Optional[str] = None
    revoked_by: str  # admin user_id or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="auth.permission_revoked",
            aggregate_id=data.get('user_id'),
            **data
        )