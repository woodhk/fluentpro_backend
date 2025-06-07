"""
Authentication request DTOs.
These DTOs define the structure of incoming requests for authentication operations.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class LoginRequest(BaseModel):
    """DTO for user login requests."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securePassword123"
            }
        }


class SignupRequest(BaseModel):
    """DTO for user signup requests."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Ensure full name contains at least two words."""
        if len(v.split()) < 2:
            raise ValueError('Full name must contain at least first and last name')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "securePassword123",
                "full_name": "John Doe"
            }
        }


class RefreshTokenRequest(BaseModel):
    """DTO for token refresh requests."""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


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
    """DTO for password change requests."""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    
    @validator('new_password')
    def passwords_different(cls, v, values):
        """Ensure new password is different from current password."""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldPassword123",
                "new_password": "newSecurePassword456"
            }
        }


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