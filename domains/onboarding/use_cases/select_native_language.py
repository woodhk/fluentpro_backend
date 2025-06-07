"""
Native language selection use case.

Handles user's native language selection during onboarding.
"""

from typing import Dict, Any
import logging

from core.exceptions import (
    ValidationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.authentication.repositories.interfaces import IUserRepository
from authentication.models.user import NativeLanguage
from domains.onboarding.services.interfaces import IProfileSetupService

logger = logging.getLogger(__name__)


class SelectNativeLanguage:
    """
    Use case for selecting user's native language.
    
    Handles native language selection and validation,
    with potential onboarding progression.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            user_repository: Repository for user operations
        """
        self.user_repository = user_repository
    
    def execute(self, auth0_id: str, language: str) -> Dict[str, Any]:
        """
        Execute native language selection.
        
        Args:
            auth0_id: Auth0 user identifier
            language: Native language code to select
            
        Returns:
            Dictionary with update result and user information
            
        Raises:
            ValidationError: If language is invalid
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If language selection fails
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
            
            # Get user by auth0_id
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Update using repository
            update_data = {'native_language': language}
            updated_user = self.user_repository.update(user.id, update_data)
            
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