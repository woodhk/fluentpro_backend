"""Authentication domain DTOs."""

from .requests import (
    LoginRequest,
    SignupRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest
)

from .responses import (
    UserResponse,
    TokenResponse,
    AuthResponse,
    UserProfileResponse,
    MessageResponse,
    RoleResponse,
    UserRole,
    OnboardingStatus
)

from .mappers import (
    UserMapper,
    RoleMapper,
    TokenMapper
)

__all__ = [
    # Requests
    'LoginRequest',
    'SignupRequest',
    'RefreshTokenRequest',
    'ChangePasswordRequest',
    'ForgotPasswordRequest',
    'ResetPasswordRequest',
    'UpdateProfileRequest',
    # Responses
    'UserResponse',
    'TokenResponse',
    'AuthResponse',
    'UserProfileResponse',
    'MessageResponse',
    'RoleResponse',
    'UserRole',
    'OnboardingStatus',
    # Mappers
    'UserMapper',
    'RoleMapper',
    'TokenMapper',
]