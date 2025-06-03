"""
Use case for user authentication and login process.
"""

from typing import Dict, Any, Optional
import logging

from core.exceptions import AuthenticationError, SupabaseUserNotFoundError, BusinessLogicError
from authentication.models.auth import TokenInfo, AuthSession
from authentication.models.user import User, UserProfile
from authentication.business.auth_manager import AuthManager
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class AuthenticateUserUseCase:
    """
    Use case for complete user authentication process.
    Handles login, token management, and user profile retrieval.
    """
    
    def __init__(
        self,
        auth_manager: Optional[AuthManager] = None,
        user_manager: Optional[UserManager] = None
    ):
        self.auth_manager = auth_manager or AuthManager()
        self.user_manager = user_manager or UserManager()
    
    def execute(
        self, 
        email: str, 
        password: str,
        client_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete user authentication process.
        
        Args:
            email: User's email address
            password: User's password
            client_info: Optional client information (IP, user agent, etc.)
            
        Returns:
            Dictionary with user data, tokens, and session info
            
        Raises:
            AuthenticationError: If authentication fails
            SupabaseUserNotFoundError: If user not found in Supabase
            BusinessLogicError: If authentication process fails
        """
        try:
            logger.info(f"Starting authentication process for email: {email}")
            
            # Step 1: Authenticate with Auth0 and get tokens
            token_info = self.auth_manager.authenticate_user(email, password)
            
            # Step 2: Get user profile from Supabase
            user = self.user_manager.get_user_by_email(email)
            if not user:
                logger.error(f"User authenticated with Auth0 but not found in Supabase: {email}")
                raise SupabaseUserNotFoundError(email)
            
            # Step 3: Get complete user profile with onboarding info
            user_profile = self.user_manager.get_user_profile(user.auth0_id)
            if not user_profile:
                # Fallback to basic user data if profile not found
                logger.warning(f"User profile not found, using basic user data: {email}")
                user_profile = UserProfile(user=user)
            
            # Step 4: Create authentication session
            session = self.auth_manager.create_auth_session(
                user=user,
                token_info=token_info,
                ip_address=client_info.get('ip_address') if client_info else None,
                user_agent=client_info.get('user_agent') if client_info else None
            )
            
            # Step 5: Determine what the user should do next
            next_actions = self._determine_next_actions(user_profile)
            
            # Step 6: Prepare comprehensive response
            response = {
                'success': True,
                'user': user_profile.to_dict(),
                'tokens': token_info.to_dict(),
                'session': {
                    'session_id': session.user_id,  # Using user_id as session identifier
                    'created_at': session.created_at.isoformat(),
                    'is_valid': session.is_valid
                },
                'onboarding': {
                    'status': user_profile.onboarding_status.value,
                    'progress_percentage': user_profile.onboarding_progress_percentage,
                    'completed': user_profile.onboarding_status.value == 'completed',
                    'next_step': next_actions.get('next_step')
                },
                'next_actions': next_actions,
                'message': 'Authentication successful'
            }
            
            logger.info(f"Authentication completed successfully for: {email}")
            return response
            
        except (AuthenticationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Authentication failed for {email}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise BusinessLogicError(f"Authentication process failed: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh user's access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dictionary with new token information
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            logger.info("Refreshing access token")
            
            # Refresh token with Auth0
            token_info = self.auth_manager.refresh_access_token(refresh_token)
            
            response = {
                'success': True,
                'tokens': token_info.to_dict(),
                'message': 'Token refreshed successfully'
            }
            
            logger.info("Token refresh completed successfully")
            return response
            
        except AuthenticationError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise BusinessLogicError(f"Token refresh failed: {str(e)}")
    
    def logout_user(
        self, 
        refresh_token: str,
        auth0_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log out user and invalidate tokens.
        
        Args:
            refresh_token: Refresh token to revoke
            auth0_id: Optional Auth0 ID for additional cleanup
            
        Returns:
            Dictionary with logout confirmation
            
        Raises:
            AuthenticationError: If logout fails
        """
        try:
            logger.info(f"Starting logout process for user: {auth0_id or 'unknown'}")
            
            # Revoke refresh token with Auth0
            self.auth_manager.logout_user(refresh_token)
            
            # Note: In a production system, you might also want to:
            # - Invalidate any cached sessions
            # - Log the logout event
            # - Clean up any temporary data
            
            response = {
                'success': True,
                'message': 'Logout successful'
            }
            
            logger.info("Logout completed successfully")
            return response
            
        except AuthenticationError as e:
            logger.warning(f"Logout failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            raise BusinessLogicError(f"Logout process failed: {str(e)}")
    
    def validate_session(self, access_token: str) -> Dict[str, Any]:
        """
        Validate user session and get current user info.
        
        Args:
            access_token: Access token to validate
            
        Returns:
            Dictionary with user info if session is valid
            
        Raises:
            AuthenticationError: If session is invalid
        """
        try:
            # Get user info from token
            auth0_user_info = self.auth_manager.get_user_info_from_token(access_token)
            
            # Get user profile from our system
            user_profile = self.user_manager.get_user_profile(auth0_user_info.get('sub'))
            if not user_profile:
                raise AuthenticationError("User session is invalid")
            
            return {
                'success': True,
                'user': user_profile.to_dict(),
                'session_valid': True,
                'message': 'Session is valid'
            }
            
        except AuthenticationError as e:
            logger.warning(f"Session validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            raise AuthenticationError("Session validation failed")
    
    def _determine_next_actions(self, user_profile: UserProfile) -> Dict[str, Any]:
        """
        Determine what actions the user should take next based on their profile.
        
        Args:
            user_profile: User's profile information
            
        Returns:
            Dictionary with next actions and recommendations
        """
        actions = {
            'next_step': None,
            'recommendations': [],
            'required_actions': [],
            'optional_actions': []
        }
        
        # Check onboarding status
        if not user_profile.has_completed_basic_info:
            actions['next_step'] = 'select_native_language'
            actions['required_actions'].append({
                'action': 'select_language',
                'title': 'Select Native Language',
                'description': 'Choose your native language for personalized content'
            })
        elif not user_profile.has_selected_industry:
            actions['next_step'] = 'select_industry'
            actions['required_actions'].append({
                'action': 'select_industry',
                'title': 'Select Industry',
                'description': 'Choose your industry for relevant role suggestions'
            })
        elif not user_profile.has_selected_role:
            actions['next_step'] = 'define_role'
            actions['required_actions'].append({
                'action': 'job_input',
                'title': 'Define Your Role',
                'description': 'Describe your job title and responsibilities'
            })
        elif user_profile.onboarding_status.value != 'completed':
            actions['next_step'] = 'communication_needs'
            actions['required_actions'].append({
                'action': 'select_communication_partners',
                'title': 'Communication Setup',
                'description': 'Define who you communicate with and in what situations'
            })
        else:
            actions['next_step'] = 'dashboard'
            actions['recommendations'].append({
                'action': 'start_learning',
                'title': 'Start Learning',
                'description': 'Begin your personalized communication training'
            })
        
        # Add optional actions based on profile completeness
        if user_profile.onboarding_status.value == 'completed':
            actions['optional_actions'].extend([
                {
                    'action': 'update_profile',
                    'title': 'Update Profile',
                    'description': 'Refine your communication preferences'
                },
                {
                    'action': 'review_progress',
                    'title': 'Review Progress',
                    'description': 'See your learning achievements and statistics'
                }
            ])
        
        return actions
    
    def get_user_dashboard_data(self, auth0_id: str) -> Dict[str, Any]:
        """
        Get dashboard data for authenticated user.
        
        Args:
            auth0_id: User's Auth0 ID
            
        Returns:
            Dictionary with dashboard information
        """
        try:
            user_profile = self.user_manager.get_user_profile(auth0_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(auth0_id)
            
            # Prepare dashboard data
            dashboard_data = {
                'user_profile': user_profile.to_dict(),
                'onboarding_status': {
                    'current_phase': user_profile.onboarding_status.value,
                    'progress_percentage': user_profile.onboarding_progress_percentage,
                    'completed': user_profile.onboarding_status.value == 'completed'
                },
                'quick_actions': self._determine_next_actions(user_profile),
                'recent_activity': [],  # Could be populated from activity logs
                'recommendations': []   # Could be populated based on user progress
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data for {auth0_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to load dashboard data: {str(e)}")