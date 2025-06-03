"""
Authentication domain models.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


class TokenType(Enum):
    """Enumeration of token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    ID = "id_token"


class AuthProvider(Enum):
    """Enumeration of authentication providers."""
    AUTH0 = "auth0"
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"


@dataclass
class TokenInfo:
    """
    Information about authentication tokens.
    """
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @property
    def expires_at(self) -> datetime:
        """Calculate when the token expires."""
        return datetime.utcnow() + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token info to dictionary for API responses."""
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'refresh_token': self.refresh_token,
            'scope': self.scope
        }


@dataclass
class AuthSession:
    """
    User authentication session information.
    """
    user_id: str
    auth0_id: str
    provider: AuthProvider
    token_info: TokenInfo
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    @property
    def session_duration(self) -> timedelta:
        """Calculate how long the session has been active."""
        return self.last_activity - self.created_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the session is valid (not expired and active)."""
        return self.is_active and not self.token_info.is_expired
    
    def update_activity(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """Update session activity timestamp and optional metadata."""
        self.last_activity = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
    
    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'user_id': self.user_id,
            'auth0_id': self.auth0_id,
            'provider': self.provider.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'session_duration_minutes': int(self.session_duration.total_seconds() / 60),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active,
            'is_valid': self.is_valid
        }


@dataclass
class LoginAttempt:
    """
    Record of a login attempt for security monitoring.
    """
    email: str
    success: bool
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    failure_reason: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.AUTH0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert login attempt to dictionary."""
        return {
            'email': self.email,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'failure_reason': self.failure_reason,
            'auth_provider': self.auth_provider.value
        }


@dataclass
class UserRegistration:
    """
    User registration data and validation.
    """
    full_name: str
    email: str
    password: str
    date_of_birth: str
    terms_accepted: bool = False
    marketing_consent: bool = False
    
    def validate(self) -> Dict[str, list]:
        """Validate registration data and return any errors."""
        from core.utils import validate_email, validate_password_strength, calculate_age
        from datetime import datetime
        
        errors = {}
        
        # Validate full name
        if not self.full_name or len(self.full_name.strip()) < 2:
            errors['full_name'] = ['Full name must be at least 2 characters']
        elif len(self.full_name) > 50:
            errors['full_name'] = ['Full name must be less than 50 characters']
        elif not self.full_name.replace(' ', '').isalpha():
            errors['full_name'] = ['Full name can only contain letters and spaces']
        
        # Validate email
        if not self.email:
            errors['email'] = ['Email is required']
        elif not validate_email(self.email):
            errors['email'] = ['Invalid email format']
        
        # Validate password
        if not self.password:
            errors['password'] = ['Password is required']
        else:
            password_validation = validate_password_strength(self.password)
            if not password_validation['is_valid']:
                errors['password'] = password_validation['errors']
        
        # Validate date of birth
        if not self.date_of_birth:
            errors['date_of_birth'] = ['Date of birth is required']
        else:
            try:
                dob = datetime.strptime(self.date_of_birth, '%Y-%m-%d').date()
                age = calculate_age(dob)
                if age < 13:
                    errors['date_of_birth'] = ['User must be at least 13 years old']
            except ValueError:
                errors['date_of_birth'] = ['Invalid date format. Use YYYY-MM-DD']
        
        # Validate terms acceptance
        if not self.terms_accepted:
            errors['terms_accepted'] = ['Terms and conditions must be accepted']
        
        return errors
    
    @property
    def is_valid(self) -> bool:
        """Check if registration data is valid."""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registration to dictionary (excluding password)."""
        return {
            'full_name': self.full_name,
            'email': self.email,
            'date_of_birth': self.date_of_birth,
            'terms_accepted': self.terms_accepted,
            'marketing_consent': self.marketing_consent
        }