from typing import Dict, Any
from supabase import Client
from ...repositories.onboarding.profile_repository import ProfileRepository
from ...models.enums import NativeLanguage, Industry
from ...core.exceptions import UserNotFoundError, DatabaseError
from ...core.logging import get_logger

logger = get_logger(__name__)


class ProfileService:
    def __init__(self, db: Client):
        self.profile_repo = ProfileRepository(db)

    async def update_native_language(
        self, auth0_id: str, native_language: NativeLanguage
    ) -> Dict[str, Any]:
        """Update user's native language."""
        try:
            # Get user by auth0_id
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                logger.warning(f"User not found with auth0_id: {auth0_id}")
                raise UserNotFoundError(auth0_id)

            # Update native language
            updated_user = await self.profile_repo.update_native_language(
                user["id"], native_language
            )

            if not updated_user:
                logger.error(f"Failed to update native language for user {user['id']}")
                raise DatabaseError("Failed to update native language")

            logger.info(
                f"Successfully updated native language to {native_language.value} for user {user['id']}"
            )

            return {
                "user_id": updated_user["id"],
                "native_language": updated_user["native_language"],
                "updated_at": updated_user["updated_at"],
            }

        except Exception as e:
            if isinstance(e, (UserNotFoundError, DatabaseError)):
                raise
            logger.error(f"Unexpected error updating native language: {str(e)}")
            raise DatabaseError("Failed to update native language")

    async def get_user_profile(self, auth0_id: str) -> Dict[str, Any]:
        """Get user profile by auth0_id."""
        try:
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                logger.warning(f"User not found with auth0_id: {auth0_id}")
                raise UserNotFoundError(auth0_id)

            return user

        except Exception as e:
            if isinstance(e, UserNotFoundError):
                raise
            logger.error(f"Unexpected error getting user profile: {str(e)}")
            raise DatabaseError("Failed to get user profile")

    async def update_industry(
        self, auth0_id: str, industry: Industry
    ) -> Dict[str, Any]:
        """Update user's industry."""
        try:
            # Get user by auth0_id
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                logger.warning(f"User not found with auth0_id: {auth0_id}")
                raise UserNotFoundError(auth0_id)

            # Get industry_id from database
            industry_id = await self.profile_repo.get_industry_id_by_name(industry)
            if not industry_id:
                logger.error(f"Industry not found: {industry.value}")
                raise DatabaseError(f"Industry {industry.value} not found")

            # Update industry
            updated_user = await self.profile_repo.update_industry(
                user["id"], industry_id
            )

            if not updated_user:
                logger.error(f"Failed to update industry for user {user['id']}")
                raise DatabaseError("Failed to update industry")

            logger.info(
                f"Successfully updated industry to {industry.value} for user {user['id']}"
            )

            return {
                "user_id": updated_user["id"],
                "industry_id": updated_user["industry_id"],
                "updated_at": updated_user["updated_at"],
            }

        except Exception as e:
            if isinstance(e, (UserNotFoundError, DatabaseError)):
                raise
            logger.error(f"Unexpected error updating industry: {str(e)}")
            raise DatabaseError("Failed to update industry")
