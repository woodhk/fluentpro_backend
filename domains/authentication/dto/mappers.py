from core.patterns.mapper import Mapper
from domains.authentication.models.user import User
from domains.authentication.dto.responses import UserResponse
from typing import List

class UserMapper(Mapper[User, UserResponse]):
    """Maps between User model and UserResponse DTO"""
    
    def to_dto(self, model: User) -> UserResponse:
        return UserResponse(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
            is_verified=self._get_is_verified(model),
            profile_completion=self._calculate_profile_completion(model),
            roles=self._get_user_roles(model)
        )
    
    def to_model(self, dto: UserResponse) -> User:
        # Note: Not all fields can be mapped back
        user = User(
            email=dto.email,
            full_name=dto.full_name,
            date_of_birth=None,  # Required field but not in DTO
            auth0_id=None  # Required field but not in DTO
        )
        user.id = dto.id
        user.is_active = dto.is_active
        return user
    
    def _calculate_profile_completion(self, user: User) -> int:
        """Calculate profile completion percentage"""
        fields = [
            user.email,
            user.full_name,
            self._get_is_verified(user),
            getattr(user, 'profile_picture', None),
            getattr(user, 'bio', None)
        ]
        completed = sum(1 for field in fields if field)
        return int((completed / len(fields)) * 100)
    
    def _get_user_roles(self, user: User) -> List[str]:
        """Get user role names"""
        # Assuming user has a roles relationship
        return [role.name for role in user.roles.all()] if hasattr(user, 'roles') else []
    
    def _get_is_verified(self, user: User) -> bool:
        """Get user verification status"""
        # Since User model doesn't have is_verified, we'll use a reasonable default
        return getattr(user, 'is_verified', False)

# Singleton instance
user_mapper = UserMapper()