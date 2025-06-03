"""
Use case for user registration and signup process.
"""

from typing import Dict, Any, Optional
import logging

from core.exceptions import ValidationError, ConflictError, BusinessLogicError
from authentication.models.auth import UserRegistration
from authentication.models.user import User, OnboardingStatus
from authentication.business.auth_manager import AuthManager
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class SignUpUserUseCase:
    """
    Use case for complete user signup process.
    Orchestrates user registration, Auth0 creation, and initial onboarding setup.
    """
    
    def __init__(
        self,
        auth_manager: Optional[AuthManager] = None,
        user_manager: Optional[UserManager] = None
    ):
        self.auth_manager = auth_manager or AuthManager()
        self.user_manager = user_manager or UserManager()
    
    def execute(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete user signup process.
        
        Args:
            registration_data: User registration information
            
        Returns:
            Dictionary with user data, tokens, and onboarding info
            
        Raises:
            ValidationError: If registration data is invalid
            ConflictError: If user already exists
            BusinessLogicError: If signup process fails
        """
        try:
            logger.info(f"Starting user signup process for email: {registration_data.get('email')}")
            
            # Step 1: Validate registration data
            registration = UserRegistration(**registration_data)
            validation_errors = registration.validate()
            
            if validation_errors:
                logger.warning(f"Signup validation failed: {validation_errors}")
                raise ValidationError("Registration validation failed", details=validation_errors)
            
            # Step 2: Check if user already exists
            existing_user = self.user_manager.get_user_by_email(registration.email)
            if existing_user:
                logger.warning(f"Signup attempted for existing user: {registration.email}")
                raise ConflictError(f"User with email '{registration.email}' already exists")
            
            # Step 3: Register user (creates Auth0 user, Supabase user, and returns tokens)
            registration_result = self.auth_manager.register_user(registration_data)
            
            # Step 4: Initialize onboarding status
            user_data = registration_result['user']
            user = User.from_supabase_data(user_data)
            
            # Update onboarding status to indicate signup completion
            try:
                self.user_manager.update_onboarding_status(
                    user.auth0_id, 
                    OnboardingStatus.BASIC_INFO
                )
            except Exception as e:
                logger.warning(f"Failed to update onboarding status after signup: {str(e)}")
                # Don't fail the entire signup process for this
            
            # Step 5: Prepare comprehensive response
            response = {
                'success': True,
                'user': user.to_dict(),
                'tokens': registration_result['tokens'],
                'onboarding': {
                    'status': OnboardingStatus.BASIC_INFO.value,
                    'next_step': 'native_language_selection',
                    'progress_percentage': 20,
                    'required': True
                },
                'message': 'User registered successfully',
                'next_actions': [
                    'Select native language',
                    'Choose industry',
                    'Define role and responsibilities'
                ]
            }
            
            logger.info(f"User signup completed successfully for: {registration.email}")
            return response
            
        except (ValidationError, ConflictError) as e:
            # Re-raise known business exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            raise BusinessLogicError(f"Signup process failed: {str(e)}")
    
    def validate_registration_data(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate registration data without creating a user.
        
        Args:
            registration_data: Registration data to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            registration = UserRegistration(**registration_data)
            validation_errors = registration.validate()
            
            if validation_errors:
                return {
                    'valid': False,
                    'errors': validation_errors,
                    'message': 'Validation failed'
                }
            
            # Check if email already exists
            existing_user = self.user_manager.get_user_by_email(registration.email)
            if existing_user:
                return {
                    'valid': False,
                    'errors': {'email': ['Email address is already registered']},
                    'message': 'Email already exists'
                }
            
            return {
                'valid': True,
                'errors': {},
                'message': 'Registration data is valid'
            }
            
        except Exception as e:
            logger.error(f"Error validating registration data: {str(e)}")
            return {
                'valid': False,
                'errors': {'general': [str(e)]},
                'message': 'Validation failed due to system error'
            }
    
    def check_email_availability(self, email: str) -> Dict[str, Any]:
        """
        Check if an email address is available for registration.
        
        Args:
            email: Email address to check
            
        Returns:
            Dictionary with availability status
        """
        try:
            from core.utils import validate_email
            
            # Validate email format
            if not validate_email(email):
                return {
                    'available': False,
                    'reason': 'Invalid email format',
                    'message': 'Please enter a valid email address'
                }
            
            # Check if email exists
            existing_user = self.user_manager.get_user_by_email(email)
            if existing_user:
                return {
                    'available': False,
                    'reason': 'Email already registered',
                    'message': 'This email address is already associated with an account'
                }
            
            return {
                'available': True,
                'reason': 'Email is available',
                'message': 'Email address is available for registration'
            }
            
        except Exception as e:
            logger.error(f"Error checking email availability: {str(e)}")
            return {
                'available': False,
                'reason': 'System error',
                'message': 'Unable to check email availability at this time'
            }
    
    def cleanup_failed_registration(self, email: str, auth0_id: Optional[str] = None) -> None:
        """
        Cleanup resources after a failed registration.
        
        Args:
            email: Email of the failed registration
            auth0_id: Auth0 ID if user was created in Auth0
        """
        try:
            logger.info(f"Cleaning up failed registration for: {email}")
            
            # Try to find and deactivate user in Supabase
            try:
                user = self.user_manager.get_user_by_email(email)
                if user:
                    self.user_manager.deactivate_user(user.auth0_id)
                    logger.info(f"Deactivated Supabase user for failed registration: {email}")
            except Exception as e:
                logger.warning(f"Failed to cleanup Supabase user: {str(e)}")
            
            # Note: We don't attempt to delete Auth0 users automatically
            # as that requires management API permissions and could cause issues
            if auth0_id:
                logger.warning(f"Auth0 user {auth0_id} may need manual cleanup")
            
        except Exception as e:
            logger.error(f"Error during registration cleanup: {str(e)}")
    
    def get_registration_requirements(self) -> Dict[str, Any]:
        """
        Get the requirements for user registration.
        
        Returns:
            Dictionary with registration requirements and validation rules
        """
        return {
            'required_fields': [
                'full_name',
                'email', 
                'password',
                'date_of_birth',
                'terms_accepted'
            ],
            'optional_fields': [
                'marketing_consent'
            ],
            'validation_rules': {
                'full_name': {
                    'min_length': 2,
                    'max_length': 50,
                    'pattern': 'Letters and spaces only'
                },
                'email': {
                    'format': 'Valid email address'
                },
                'password': {
                    'min_length': 8,
                    'requirements': [
                        'At least one uppercase letter',
                        'At least one lowercase letter', 
                        'At least one number',
                        'At least one special character'
                    ]
                },
                'date_of_birth': {
                    'format': 'YYYY-MM-DD',
                    'min_age': 13
                },
                'terms_accepted': {
                    'required': True,
                    'value': True
                }
            },
            'next_steps_after_signup': [
                'Email verification (if enabled)',
                'Select native language',
                'Choose industry',
                'Define role and job responsibilities',
                'Select communication partners and situations'
            ]
        }