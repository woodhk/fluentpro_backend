"""
User-related domain events for the authentication domain.
These events represent significant user lifecycle events.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from domains.shared.events.base_event import DomainEvent


class UserRegisteredEvent(DomainEvent):
    """Event raised when a new user registers in the system."""
    
    user_id: str = Field(..., description="Unique identifier of the registered user")
    email: str = Field(..., description="Email address of the registered user")
    full_name: str = Field(..., description="Full name of the registered user")
    auth0_id: str = Field(..., description="Auth0 unique identifier for the user")
    registration_source: str = Field(default="web", description="Source of registration (web, mobile, api)")
    event_type: str = Field(default="user.registered", description="Type of the event")
    
    def __init__(self, **data):
        # Set aggregate_id to user_id if not provided
        if 'aggregate_id' not in data and 'user_id' in data:
            data['aggregate_id'] = data['user_id']
        super().__init__(**data)


class UserLoggedInEvent(DomainEvent):
    """Event raised when a user successfully logs in."""
    
    user_id: str
    email: str
    login_method: str = "email_password"  # email_password, oauth, sso
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.logged_in",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserLoggedOutEvent(DomainEvent):
    """Event raised when a user logs out."""
    
    user_id: str
    session_id: Optional[str] = None
    logout_reason: str = "user_initiated"  # user_initiated, session_expired, forced
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.logged_out",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserProfileUpdatedEvent(DomainEvent):
    """Event raised when a user updates their profile."""
    
    user_id: str
    updated_fields: list
    previous_values: dict
    new_values: dict
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.profile_updated",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserPasswordChangedEvent(DomainEvent):
    """Event raised when a user changes their password."""
    
    user_id: str
    email: str
    change_method: str = "self_service"  # self_service, admin_reset, forced_reset
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.password_changed",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserPasswordResetRequestedEvent(DomainEvent):
    """Event raised when a user requests a password reset."""
    
    user_id: str
    email: str
    reset_token: str
    expires_at: datetime
    request_ip: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.password_reset_requested",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserPasswordResetCompletedEvent(DomainEvent):
    """Event raised when a user completes a password reset."""
    
    user_id: str
    email: str
    reset_token: str
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.password_reset_completed",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserAccountActivatedEvent(DomainEvent):
    """Event raised when a user account is activated."""
    
    user_id: str
    email: str
    activation_method: str = "email_verification"  # email_verification, admin_approval
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.account_activated",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserAccountDeactivatedEvent(DomainEvent):
    """Event raised when a user account is deactivated."""
    
    user_id: str
    email: str
    deactivation_reason: str
    deactivated_by: str  # user_id of admin or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.account_deactivated",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserEmailVerifiedEvent(DomainEvent):
    """Event raised when a user verifies their email address."""
    
    user_id: str
    email: str
    verification_token: str
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.email_verified",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserRoleAssignedEvent(DomainEvent):
    """Event raised when a role is assigned to a user."""
    
    user_id: str
    role_id: str
    role_name: str
    assigned_by: str  # user_id of admin or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.role_assigned",
            aggregate_id=data.get('user_id'),
            **data
        )


class UserRoleRevokedEvent(DomainEvent):
    """Event raised when a role is revoked from a user."""
    
    user_id: str
    role_id: str
    role_name: str
    revoked_by: str  # user_id of admin or "system"
    
    def __init__(self, **data):
        super().__init__(
            event_type="user.role_revoked",
            aggregate_id=data.get('user_id'),
            **data
        )