"""
Business logic for user management operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from core.exceptions import (
    SupabaseUserNotFoundError,
    ValidationError,
    ConflictError,
    BusinessLogicError
)
from core.responses import ServiceResponse
from core.interfaces import UserRepositoryInterface, IndustryRepositoryInterface
from core.services import ServiceMixin
from authentication.models.user import User, UserProfile, NativeLanguage, OnboardingStatus
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class UserManager(ServiceMixin):
    """
    Business logic manager for user operations.
    Handles user CRUD operations and profile management.
    """
    
    def __init__(
        self,
        user_repository: Optional[UserRepositoryInterface] = None,
        industry_repository: Optional[IndustryRepositoryInterface] = None
    ):
        super().__init__()
        self.user_repository = user_repository or self.services.users
        self.industry_repository = industry_repository or self.services.industries
        self.supabase_service = SupabaseService()
    
    def get_user_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """
        Get user by Auth0 ID.
        
        Args:
            auth0_id: Auth0 user identifier
            
        Returns:
            User instance or None if not found
        """
        try:
            return self.user_repository.get_by_auth0_id(auth0_id)
            
        except Exception as e:
            logger.error(f"Failed to get user by Auth0 ID {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve user: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User instance or None if not found
        """
        try:
            # Use repository pattern instead of direct service call
            return self.user_repository.get_by_email(email)
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve user: {str(e)}")
    
    def get_user_profile(self, auth0_id: str) -> Optional[UserProfile]:
        """
        Get complete user profile with onboarding information.
        
        Args:
            auth0_id: Auth0 user identifier
            
        Returns:
            UserProfile instance or None if not found
        """
        try:
            # Get user first to get user ID
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                return None
            
            # Get profile using user ID
            return self.user_repository.get_profile(user.id)
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve user profile: {str(e)}")
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created User instance
            
        Raises:
            ConflictError: If user with email already exists
            ValidationError: If user data is invalid
        """
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(user_data['email'])
            if existing_user:
                raise ConflictError(f"User with email '{user_data['email']}' already exists")
            
            # Create user using repository
            return self.user_repository.create(user_data)
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise BusinessLogicError(f"Failed to create user: {str(e)}")
    
    def update_native_language(self, auth0_id: str, language: str) -> Dict[str, Any]:
        """
        Update user's native language.
        
        Args:
            auth0_id: Auth0 user identifier
            language: Native language code
            
        Returns:
            Update result with user information
            
        Raises:
            ValidationError: If language is invalid
            SupabaseUserNotFoundError: If user not found
        """
        try:
            # Validate language
            try:
                native_language = NativeLanguage(language)
            except ValueError:
                valid_languages = [lang.value for lang in NativeLanguage]
                raise ValidationError(
                    f"Invalid language '{language}'. Must be one of: {', '.join(valid_languages)}"
                )
            
            # Get user by auth0_id first
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Update using repository
            update_data = {'native_language': language}
            updated_user = self.user_repository.update(user.id, update_data)
            
            # Check if we should advance to personalisation phase
            self._check_and_advance_basic_info_phase(auth0_id)
            
            return {
                'success': True,
                'user_id': updated_user.id,
                'native_language': language
            }
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to update native language for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update native language: {str(e)}")
    
    def update_industry(self, auth0_id: str, industry_id: str) -> Dict[str, Any]:
        """
        Update user's industry by ID.
        
        Args:
            auth0_id: Auth0 user identifier
            industry_id: Industry identifier
            
        Returns:
            Update result with industry information
            
        Raises:
            ValidationError: If industry is invalid
            SupabaseUserNotFoundError: If user not found
        """
        try:
            # Validate industry exists
            industry = self.industry_repository.get_by_id(industry_id)
            if not industry:
                raise ValidationError(f"Industry with ID '{industry_id}' not found")
            
            # Get user by auth0_id first
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Update using repository
            update_data = {'industry_id': industry_id}
            updated_user = self.user_repository.update(user.id, update_data)
            
            # Check if we should advance to personalisation phase
            self._check_and_advance_basic_info_phase(auth0_id)
            
            return {
                'success': True,
                'user_id': updated_user.id,
                'industry_id': industry_id,
                'industry_name': industry.get('name')
            }
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to update industry for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update industry: {str(e)}")
    
    def update_industry_by_name(self, auth0_id: str, industry_name: str) -> Dict[str, Any]:
        """
        Update user's industry by name.
        
        Args:
            auth0_id: Auth0 user identifier
            industry_name: Industry name
            
        Returns:
            Update result with industry information
            
        Raises:
            ValidationError: If industry is invalid
            SupabaseUserNotFoundError: If user not found
        """
        try:
            # Validate industry exists by name
            industry = self.industry_repository.get_by_name(industry_name)
            if not industry:
                raise ValidationError(f"Industry with name '{industry_name}' not found")
            
            # Use the existing update_industry method with the found industry_id
            return self.update_industry(auth0_id, industry['id'])
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to update industry by name for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update industry: {str(e)}")
    
    def update_selected_role(self, auth0_id: str, role_id: str) -> Dict[str, Any]:
        """
        Update user's selected role.
        
        Args:
            auth0_id: Auth0 user identifier
            role_id: Role identifier
            
        Returns:
            Update result with role information
            
        Raises:
            ValidationError: If role is invalid
            SupabaseUserNotFoundError: If user not found
        """
        try:
            # First validate that the role exists (assuming we have a role repository in services)
            role_repository = self.services.roles if hasattr(self.services, 'roles') else None
            if role_repository:
                role = role_repository.get_by_id(role_id)
                if not role:
                    raise ValidationError(f"Role with ID '{role_id}' not found")
            
            # Get user by auth0_id first
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Update using repository
            update_data = {'selected_role_id': role_id}
            updated_user = self.user_repository.update(user.id, update_data)
            
            # Check if we should advance to personalisation phase
            self._check_and_advance_basic_info_phase(auth0_id)
            
            # Get role title for response (if role repository available)
            role_title = role.title if role_repository and role else None
            
            return {
                'success': True,
                'user_id': updated_user.id,
                'role_id': role_id,
                'role_title': role_title
            }
            
        except (ValidationError, SupabaseUserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to update selected role for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update selected role: {str(e)}")
    
    def update_onboarding_status(self, auth0_id: str, new_status: OnboardingStatus) -> None:
        """
        Update user's onboarding status.
        
        Args:
            auth0_id: Auth0 user identifier
            new_status: New onboarding status
            
        Raises:
            SupabaseUserNotFoundError: If user not found
            ValidationError: If status progression is invalid
        """
        try:
            # Get current user profile to validate progression
            user_profile = self.get_user_profile(auth0_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Validate status progression
            user_profile.advance_onboarding_status(new_status)
            
            # Update in database using repository
            update_data = {'onboarding_status': new_status.value}
            self.user_repository.update(user_profile.user.id, update_data)
            
        except (SupabaseUserNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update onboarding status for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update onboarding status: {str(e)}")
    
    def can_access_feature(self, auth0_id: str, required_status: OnboardingStatus) -> bool:
        """
        Check if user can access a feature based on onboarding status.
        
        Args:
            auth0_id: Auth0 user identifier
            required_status: Required onboarding status
            
        Returns:
            True if user can access the feature
        """
        try:
            user_profile = self.get_user_profile(auth0_id)
            if not user_profile:
                return False
            
            return user_profile.can_access_phase(required_status)
            
        except Exception as e:
            logger.error(f"Failed to check feature access for {auth0_id}: {str(e)}")
            return False
    
    def get_available_industries(self) -> List[Dict[str, Any]]:
        """
        Get list of available industries for selection.
        
        Returns:
            List of industry dictionaries
        """
        try:
            return self.industry_repository.get_all()
            
        except Exception as e:
            logger.error(f"Failed to get available industries: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve industries: {str(e)}")
    
    def deactivate_user(self, auth0_id: str) -> None:
        """
        Deactivate a user account.
        
        Args:
            auth0_id: Auth0 user identifier
            
        Raises:
            SupabaseUserNotFoundError: If user not found
        """
        try:
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            result = self.supabase_service.delete_user(user.id)
            if not result:
                raise BusinessLogicError("Failed to deactivate user account")
            
        except SupabaseUserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate user {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to deactivate user: {str(e)}")
    
    def _update_user_session_phase(self, auth0_id: str, new_phase: str) -> None:
        """
        Update user session phase.
        
        Args:
            auth0_id: Auth0 user identifier
            new_phase: New session phase
        """
        try:
            # Get user by auth0_id
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                logger.warning(f"User not found for session phase update: {auth0_id}")
                return
            
            # Update user session phase in database
            self.supabase_service.client.table('user_sessions')\
                .update({'phase': new_phase, 'updated_at': datetime.utcnow().isoformat()})\
                .eq('user_id', user.id)\
                .eq('is_active', True)\
                .execute()
            
            logger.info(f"Updated session phase to '{new_phase}' for user {user.id}")
            
        except Exception as e:
            logger.error(f"Failed to update session phase for {auth0_id}: {str(e)}")
            # Don't raise here - session phase update is not critical enough to fail the main operation
    
    def _check_and_advance_basic_info_phase(self, auth0_id: str) -> None:
        """
        Check if basic info is complete and advance to personalisation phase.
        
        Args:
            auth0_id: Auth0 user identifier
        """
        try:
            user_profile = self.get_user_profile(auth0_id)
            if not user_profile:
                return
            
            # Check if all basic info is completed
            if (user_profile.native_language and 
                user_profile.industry_id and 
                user_profile.selected_role_id):
                
                # Update both session phase and onboarding status
                self._update_user_session_phase(auth0_id, 'personalisation')
                self.update_onboarding_status(auth0_id, OnboardingStatus.PERSONALISATION)
                logger.info(f"Advanced user {auth0_id} to personalisation phase and status")
                
        except Exception as e:
            logger.error(f"Failed to check basic info completion for {auth0_id}: {str(e)}")