"""
User industry selection use case.

Handles user's industry selection during onboarding.
"""

from typing import Dict, Any
import logging

from core.exceptions import (
    ValidationError,
    SupabaseUserNotFoundError,
    BusinessLogicError
)
from domains.shared.repositories.interfaces import IUserRepository
from domains.onboarding.repositories.interfaces import IIndustryRepository
from domains.onboarding.services.interfaces import IProfileSetupService

logger = logging.getLogger(__name__)


class SelectUserIndustry:
    """
    Selects and assigns an industry to a user profile.
    
    Flow:
    1. Validate industry selection (either ID or name required)
    2. Look up industry by ID or name in repository
    3. Find user by Auth0 ID
    4. Update user profile with selected industry
    5. Return success response with industry details
    
    Errors:
    - ValidationError: Missing industry or invalid industry ID/name
    - SupabaseUserNotFoundError: User not found by Auth0 ID
    - BusinessLogicError: Failed to update user industry
    
    Dependencies:
    - IUserRepository: To find and update user profile
    - IIndustryRepository: To validate and retrieve industry data
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        industry_repository: IIndustryRepository
    ):
        """
        Initialize with injected dependencies.
        
        Args:
            user_repository: Repository for user operations
            industry_repository: Repository for industry operations
        """
        self.user_repository = user_repository
        self.industry_repository = industry_repository
    
    def execute(self, auth0_id: str, industry_id: str = None, industry_name: str = None) -> Dict[str, Any]:
        """
        Execute industry selection.
        
        Args:
            auth0_id: Auth0 user identifier
            industry_id: Industry identifier (optional if industry_name provided)
            industry_name: Industry name (optional if industry_id provided)
            
        Returns:
            Dictionary with update result and industry information
            
        Raises:
            ValidationError: If industry is invalid or missing
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If industry selection fails
        """
        try:
            if not industry_id and not industry_name:
                raise ValidationError("Either industry_id or industry_name must be provided")
            
            # Get industry by ID or name
            if industry_id:
                industry = self.industry_repository.get_by_id(industry_id)
                if not industry:
                    raise ValidationError(f"Industry with ID '{industry_id}' not found")
            else:
                industry = self.industry_repository.get_by_name(industry_name)
                if not industry:
                    raise ValidationError(f"Industry with name '{industry_name}' not found")
                industry_id = industry['id']
            
            # Get user by auth0_id
            user = self.user_repository.get_by_auth0_id(auth0_id)
            if not user:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Update using repository
            update_data = {'industry_id': industry_id}
            updated_user = self.user_repository.update(user.id, update_data)
            
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