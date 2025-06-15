from typing import Dict, Any, Optional
from datetime import date
from ...integrations.auth0 import Auth0ManagementClient
from ..users.user_service import UserService
from ..onboarding.onboarding_progress_service import OnboardingProgressService
from ...core.exceptions import AuthenticationError, UserNotFoundError
from ...utils.validators import (
    is_valid_email,
    is_strong_password,
    normalize_email,
    sanitize_string,
    is_valid_date_of_birth,
)
from supabase import Client
from ...core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Centralized authentication service for user auth operations"""

    def __init__(self, db: Client):
        self.db = db
        self.auth0_client = Auth0ManagementClient()
        self.user_service = UserService(db)
        self.progress_service = OnboardingProgressService(db)

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user and get access token
        1. Validate input
        2. Authenticate with Auth0
        3. Get or create user in Supabase
        4. Return token and user data
        """
        try:
            # Validate and normalize input
            email = normalize_email(email)
            if not is_valid_email(email):
                raise AuthenticationError("Invalid email format")

            if not password:
                raise AuthenticationError("Password is required")

            # Authenticate with Auth0
            auth_result = await self.auth0_client.authenticate_user(email, password)
            
            # Extract the Auth0 user ID from the access token
            from ...core.auth import auth0_validator
            token_payload = auth0_validator.verify_jwt_token(auth_result["access_token"])
            auth0_id = token_payload["sub"]

            # Get or create user in Supabase
            user = await self.get_or_create_user(auth0_id)

            return {
                "success": True,
                "message": "Login successful",
                "access_token": auth_result["access_token"],
                "user": user,
            }

        except Exception as e:
            raise AuthenticationError(f"Login failed: {str(e)}")

    async def signup_user(
        self, email: str, password: str, full_name: str, date_of_birth: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Complete user signup process
        1. Create user in Auth0
        2. Create user in Supabase
        3. Initialize onboarding progress
        4. Return success response
        """
        try:
            # Validate and normalize input
            email = normalize_email(email)
            if not is_valid_email(email):
                raise AuthenticationError("Invalid email format")

            is_valid_pwd, pwd_error = is_strong_password(password)
            if not is_valid_pwd:
                raise AuthenticationError(pwd_error)

            full_name = sanitize_string(full_name, max_length=100)
            if len(full_name) < 2:
                raise AuthenticationError("Name must be at least 2 characters long")

            # Validate date of birth if provided
            if date_of_birth:
                is_valid_dob, dob_error = is_valid_date_of_birth(date_of_birth)
                if not is_valid_dob:
                    raise AuthenticationError(dob_error)

            # Create user in Auth0
            auth0_user = await self.auth0_client.create_user(
                email=email, password=password, name=full_name
            )

            # Create user in Supabase
            user_data = {
                "sub": auth0_user["user_id"],
                "email": auth0_user["email"],
                "name": auth0_user.get("name", full_name),
            }

            supabase_user = await self.user_service.create_user_from_auth0(user_data, date_of_birth=date_of_birth)

            # Initialize onboarding progress for new user
            try:
                await self.progress_service.progress_repo.upsert_progress(
                    user_id=supabase_user["id"],
                    current_step="not_started",
                    data={"signup_date": "now()"},
                    completed=False,
                )
                logger.info(
                    f"Initialized onboarding progress for new user {supabase_user['id']}"
                )
            except Exception as e:
                # Don't fail signup if progress initialization fails
                logger.error(f"Failed to initialize onboarding progress: {str(e)}")

            return {
                "success": True,
                "message": "User created successfully",
                "user_id": supabase_user["id"],
                "auth0_id": auth0_user["user_id"],
            }

        except Exception as e:
            raise AuthenticationError(f"Signup failed: {str(e)}")

    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user from Supabase by Auth0 ID"""
        return await self.user_service.get_user_by_auth0_id(auth0_id)

    async def get_or_create_user(self, auth0_id: str) -> Dict[str, Any]:
        """
        Get user by Auth0 ID, or create if doesn't exist
        Used by authentication dependencies
        """
        try:
            # Check if user exists in Supabase
            existing_user = await self.get_user_by_auth0_id(auth0_id)

            if existing_user:
                # Check if they have onboarding progress (for backwards compatibility)
                try:
                    progress = (
                        await self.progress_service.progress_repo.get_user_progress(
                            existing_user["id"]
                        )
                    )
                    if not progress:
                        # Create progress for existing users who don't have it
                        await self.progress_service.progress_repo.upsert_progress(
                            user_id=existing_user["id"],
                            current_step="not_started",
                            data={"created_for_existing_user": True},
                            completed=False,
                        )
                        logger.info(
                            f"Created onboarding progress for existing user {existing_user['id']}"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to check/create progress for existing user: {str(e)}"
                    )

                return existing_user

            # User doesn't exist, fetch from Auth0 and create in Supabase
            auth0_profile = await self.auth0_client.get_user_profile(auth0_id)

            if not auth0_profile:
                raise UserNotFoundError(f"User not found in Auth0: {auth0_id}")

            # Create user in Supabase
            user_data = {
                "sub": auth0_profile.get("user_id"),
                "email": auth0_profile.get("email"),
                "name": auth0_profile.get("name"),
            }

            new_user = await self.user_service.create_user_from_auth0(user_data)

            # Initialize onboarding progress for new user
            try:
                await self.progress_service.progress_repo.upsert_progress(
                    user_id=new_user["id"],
                    current_step="not_started",
                    data={"created_via_auth0": True},
                    completed=False,
                )
                logger.info(
                    f"Initialized onboarding progress for Auth0 user {new_user['id']}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize onboarding progress: {str(e)}")

            return new_user

        except Exception as e:
            raise AuthenticationError(f"Failed to get or create user: {str(e)}")

    async def sync_user_profile(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """
        Sync user profile from Auth0 to Supabase
        Future: Will be used for email verification updates, profile changes
        """
        try:
            # Get latest profile from Auth0
            auth0_profile = await self.auth0_client.get_user_profile(auth0_id)

            if not auth0_profile:
                return None

            # Update user in Supabase
            return await self.user_service.sync_auth0_profile(auth0_id)

        except Exception as e:
            raise AuthenticationError(f"Failed to sync user profile: {str(e)}")

    # Future methods for password reset and email verification

    async def initiate_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Initiate password reset flow
        TODO: Implement when needed
        """
        # Will use Auth0 Management API to trigger password reset
        raise NotImplementedError("Password reset not yet implemented")

    async def verify_email(self, auth0_id: str) -> Dict[str, Any]:
        """
        Handle email verification
        TODO: Implement when needed
        """
        # Will update email_verified status in Auth0 and sync to Supabase
        raise NotImplementedError("Email verification not yet implemented")

    async def resend_verification_email(self, auth0_id: str) -> Dict[str, Any]:
        """
        Resend email verification
        TODO: Implement when needed
        """
        # Will use Auth0 Management API to resend verification email
        raise NotImplementedError("Resend verification not yet implemented")
