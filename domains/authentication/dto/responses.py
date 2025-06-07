"""
Authentication response DTOs.
These DTOs define the structure of responses from authentication operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class OnboardingStatus(str, Enum):
    """User onboarding status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class UserResponse(BaseModel):
    """DTO for user data in responses."""
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether the user account is active")
    onboarding_status: OnboardingStatus = Field(OnboardingStatus.PENDING, description="User's onboarding status")
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.USER], description="User's roles")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "is_active": True,
                "onboarding_status": "completed",
                "roles": ["user"]
            }
        }


class TokenResponse(BaseModel):
    """DTO for authentication token responses."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class AuthResponse(BaseModel):
    """DTO for authentication responses combining user data and tokens."""
    user: UserResponse = Field(..., description="Authenticated user data")
    tokens: TokenResponse = Field(..., description="Authentication tokens")
    
    class Config:
        schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "created_at": "2024-01-15T10:30:00Z",
                    "is_active": True,
                    "onboarding_status": "completed",
                    "roles": ["user"]
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600
                }
            }
        }


class UserProfileResponse(BaseModel):
    """DTO for detailed user profile responses."""
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    bio: Optional[str] = Field(None, description="User bio or description")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether the user account is active")
    onboarding_status: OnboardingStatus = Field(..., description="User's onboarding status")
    roles: List[UserRole] = Field(default_factory=list, description="User's roles")
    
    # Profile-specific fields
    native_language: Optional[str] = Field(None, description="User's native language")
    learning_language: Optional[str] = Field(None, description="Language the user is learning")
    proficiency_level: Optional[str] = Field(None, description="User's proficiency level")
    selected_industry: Optional[str] = Field(None, description="User's selected industry")
    selected_role: Optional[str] = Field(None, description="User's selected professional role")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "bio": "Language learning enthusiast",
                "avatar_url": "https://example.com/avatar.jpg",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "is_active": True,
                "onboarding_status": "completed",
                "roles": ["user"],
                "native_language": "English",
                "learning_language": "Spanish",
                "proficiency_level": "intermediate",
                "selected_industry": "Technology",
                "selected_role": "Software Engineer"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response DTO."""
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Whether the operation was successful")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }


class RoleResponse(BaseModel):
    """DTO for role data in responses."""
    id: str = Field(..., description="Role's unique identifier")
    title: str = Field(..., description="Role title")
    description: str = Field(..., description="Role description")
    hierarchy_level: str = Field(..., description="Role hierarchy level")
    industry_id: str = Field(..., description="Associated industry ID")
    industry_name: Optional[str] = Field(None, description="Associated industry name")
    is_custom: bool = Field(False, description="Whether this is a custom role")
    created_at: datetime = Field(..., description="Role creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "title": "Software Engineer",
                "description": "Develops and maintains software applications",
                "hierarchy_level": "mid-level",
                "industry_id": "789e0123-e89b-12d3-a456-426614174000",
                "industry_name": "Technology",
                "is_custom": False,
                "created_at": "2024-01-10T08:00:00Z"
            }
        }