"""
Authentication DTO mappers.
These mappers handle conversion between domain models and DTOs.
"""

from typing import List, Optional
from datetime import datetime

from domains.authentication.models.user import User, UserProfile
from domains.authentication.models.role import Role
from domains.authentication.dto.responses import (
    UserResponse,
    UserProfileResponse,
    RoleResponse,
    TokenResponse,
    AuthResponse,
    OnboardingStatus as DTOOnboardingStatus,
    UserRole
)


class UserMapper:
    """Mapper for User model to DTOs."""
    
    @staticmethod
    def to_response(user: User) -> UserResponse:
        """Convert User model to UserResponse DTO."""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
            onboarding_status=DTOOnboardingStatus(user.onboarding_status.value),
            roles=[UserRole.USER]  # Default role, can be extended based on business logic
        )
    
    @staticmethod
    def to_profile_response(user: User, profile: Optional[UserProfile] = None) -> UserProfileResponse:
        """Convert User model and UserProfile to UserProfileResponse DTO."""
        response_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "is_active": user.is_active,
            "onboarding_status": DTOOnboardingStatus(user.onboarding_status.value),
            "roles": [UserRole.USER]  # Default role
        }
        
        # Add profile data if available
        if profile:
            response_data.update({
                "bio": profile.bio,
                "avatar_url": profile.avatar_url,
                "native_language": profile.native_language,
                "learning_language": profile.learning_language,
                "proficiency_level": profile.proficiency_level,
                "selected_industry": profile.industry_name if hasattr(profile, 'industry_name') else None,
                "selected_role": profile.role_title if hasattr(profile, 'role_title') else None
            })
        
        return UserProfileResponse(**response_data)
    
    @staticmethod
    def from_signup_request(signup_data: dict) -> dict:
        """Convert signup request data to user creation data."""
        return {
            "email": signup_data["email"],
            "full_name": signup_data["full_name"],
            "password": signup_data["password"],  # This should be hashed in the service layer
            "is_active": True,
            "onboarding_status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }


class RoleMapper:
    """Mapper for Role model to DTOs."""
    
    @staticmethod
    def to_response(role: Role) -> RoleResponse:
        """Convert Role model to RoleResponse DTO."""
        return RoleResponse(
            id=role.id,
            title=role.title,
            description=role.description,
            hierarchy_level=role.hierarchy_level.value,
            industry_id=role.industry_id,
            industry_name=role.industry.name if role.industry else None,
            is_custom=role.is_custom,
            created_at=role.created_at
        )
    
    @staticmethod
    def to_response_list(roles: List[Role]) -> List[RoleResponse]:
        """Convert list of Role models to list of RoleResponse DTOs."""
        return [RoleMapper.to_response(role) for role in roles]


class TokenMapper:
    """Mapper for token-related data."""
    
    @staticmethod
    def to_token_response(access_token: str, refresh_token: str, expires_in: int = 3600) -> TokenResponse:
        """Create TokenResponse DTO from token data."""
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=expires_in
        )
    
    @staticmethod
    def to_auth_response(user: User, access_token: str, refresh_token: str, expires_in: int = 3600) -> AuthResponse:
        """Create AuthResponse DTO combining user and token data."""
        return AuthResponse(
            user=UserMapper.to_response(user),
            tokens=TokenMapper.to_token_response(access_token, refresh_token, expires_in)
        )