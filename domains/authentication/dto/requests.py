"""
Authentication request DTOs.
These DTOs define the structure of incoming requests for authentication operations.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class LoginRequest(BaseModel):
    """Login request DTO"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    remember_me: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "remember_me": True
            }
        }


class SignupRequest(BaseModel):
    """User registration request DTO"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str
    full_name: str = Field(..., min_length=2, max_length=100)
    accept_terms: bool
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('accept_terms')
    def terms_accepted(cls, v):
        if not v:
            raise ValueError('Terms must be accepted')
        return v


class RefreshTokenRequest(BaseModel):
    """Token refresh request DTO"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """DTO for logout requests."""
    refresh_token: str = Field(..., description="JWT refresh token to revoke")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request DTO"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ForgotPasswordRequest(BaseModel):
    """DTO for forgot password requests."""
    email: EmailStr = Field(..., description="Email address to send reset link")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """DTO for password reset requests."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-from-email",
                "new_password": "newSecurePassword789"
            }
        }


class UpdateProfileRequest(BaseModel):
    """DTO for profile update requests."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    bio: Optional[str] = Field(None, max_length=500, description="User bio or description")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Ensure full name contains at least two words if provided."""
        if v and len(v.split()) < 2:
            raise ValueError('Full name must contain at least first and last name')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Jane Smith",
                "bio": "Language learning enthusiast",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }