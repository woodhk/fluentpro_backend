from typing import Dict, Any, Optional
from ...integrations.auth0 import Auth0ManagementClient
from ..users.user_service import UserService
from ...core.exceptions import AuthenticationError, UserNotFoundError
from ...utils.validators import is_valid_email, is_strong_password, normalize_email, sanitize_string
from supabase import Client


class AuthService:
    """Centralized authentication service for user auth operations"""
    
    def __init__(self, db: Client):
        self.db = db
        self.auth0_client = Auth0ManagementClient()
        self.user_service = UserService(db)
    
    async def signup_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Complete user signup process
        1. Create user in Auth0
        2. Create user in Supabase
        3. Return success response
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
            
            # Create user in Auth0
            auth0_user = await self.auth0_client.create_user(
                email=email,
                password=password,
                name=full_name
            )
            
            # Create user in Supabase
            user_data = {
                "sub": auth0_user["user_id"],
                "email": auth0_user["email"],
                "name": auth0_user.get("name", full_name)
            }
            
            supabase_user = await self.user_service.create_user_from_auth0(user_data)
            
            return {
                "success": True,
                "message": "User created successfully",
                "user_id": supabase_user["id"],
                "auth0_id": auth0_user["user_id"]
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
                return existing_user
            
            # User doesn't exist, fetch from Auth0 and create in Supabase
            auth0_profile = await self.auth0_client.get_user_profile(auth0_id)
            
            if not auth0_profile:
                raise UserNotFoundError(f"User not found in Auth0: {auth0_id}")
            
            # Create user in Supabase
            user_data = {
                "sub": auth0_profile.get("user_id"),
                "email": auth0_profile.get("email"),
                "name": auth0_profile.get("name")
            }
            
            return await self.user_service.create_user_from_auth0(user_data)
            
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