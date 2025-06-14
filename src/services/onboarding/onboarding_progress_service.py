from typing import Dict, Any, Optional
from supabase import Client
from ...repositories.onboarding.onboarding_progress_repository import (
    OnboardingProgressRepository,
)
from ...repositories.onboarding.profile_repository import ProfileRepository
from ...core.redis_client import onboarding_redis
from ...core.logging import get_logger
from ...core.exceptions import DatabaseError, UserNotFoundError

logger = get_logger(__name__)


class OnboardingProgressService:
    """Service for managing onboarding progress tracking."""

    # Step progression mapping
    STEP_ORDER = [
        "not_started",
        "native_language",
        "industry_selection",
        "role_input",
        "role_selection",
        "communication_partners",
        "situation_selection",
        "summary",
        "completed",
    ]

    # Map API actions to progress steps
    ACTION_TO_STEP = {
        "set_native_language": "native_language",
        "set_industry": "industry_selection",
        "search_roles": "role_input",
        "select_role": "role_selection",
        "select_communication_partners": "communication_partners",
        "select_situations": "situation_selection",
        "view_summary": "summary",
        "complete_onboarding": "completed",
    }

    def __init__(self, db: Client):
        self.progress_repo = OnboardingProgressRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def get_user_progress(self, auth0_id: str) -> Dict[str, Any]:
        """Get user's onboarding progress, checking Redis first."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise UserNotFoundError(f"User not found: {auth0_id}")

            # Check Redis cache first
            cached_progress = onboarding_redis.get_progress(user["id"])
            if cached_progress:
                # Extend TTL for active user
                onboarding_redis.extend_ttl(user["id"])
                return cached_progress

            # Fallback to database
            progress = await self.progress_repo.get_user_progress(user["id"])

            if not progress:
                # Create initial progress record
                progress = await self.progress_repo.upsert_progress(
                    user_id=user["id"],
                    current_step="not_started",
                    data={},
                    completed=False,
                )

            # Cache in Redis
            if progress:
                onboarding_redis.set_progress(user["id"], progress)

            return progress

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get onboarding progress: {str(e)}")
            raise DatabaseError(f"Failed to retrieve progress: {str(e)}")

    async def update_progress_on_action(
        self, auth0_id: str, action: str, action_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update progress based on successful API action."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise UserNotFoundError(f"User not found: {auth0_id}")

            # Get current progress
            current_progress = await self.get_user_progress(auth0_id)

            # Determine new step based on action
            new_step = self.ACTION_TO_STEP.get(action)
            if not new_step:
                logger.warning(f"Unknown action: {action}")
                return current_progress

            # Check if this is forward progress
            current_index = self.STEP_ORDER.index(current_progress["current_step"])
            new_index = self.STEP_ORDER.index(new_step)

            # Only update step if moving forward
            if new_index > current_index:
                progress_step = new_step
            else:
                progress_step = current_progress["current_step"]

            # Merge action data into existing data
            updated_data = current_progress.get("data", {})
            if action_data:
                # Add timestamp for tracking
                action_data["updated_at"] = "now()"
                updated_data[action] = action_data

            # Check if completed
            is_completed = new_step == "completed"

            # Update in database
            updated_progress = await self.progress_repo.upsert_progress(
                user_id=user["id"],
                current_step=progress_step,
                data=updated_data,
                completed=is_completed,
            )

            # Update Redis cache
            onboarding_redis.set_progress(user["id"], updated_progress)

            logger.info(
                f"Updated progress for user {user['id']}: action={action}, step={progress_step}"
            )

            return updated_progress

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update onboarding progress: {str(e)}")
            raise DatabaseError(f"Failed to update progress: {str(e)}")

    async def get_next_step(self, auth0_id: str) -> str:
        """Get the next step for the user to complete."""
        try:
            progress = await self.get_user_progress(auth0_id)
            current_step = progress["current_step"]

            if current_step == "completed":
                return "completed"

            current_index = self.STEP_ORDER.index(current_step)
            next_index = min(current_index + 1, len(self.STEP_ORDER) - 1)

            return self.STEP_ORDER[next_index]

        except Exception as e:
            logger.error(f"Failed to get next step: {str(e)}")
            return "not_started"

    async def reset_progress(self, auth0_id: str) -> Dict[str, Any]:
        """Reset user's onboarding progress (admin function)."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise UserNotFoundError(f"User not found: {auth0_id}")

            # Reset in database
            reset_progress = await self.progress_repo.upsert_progress(
                user_id=user["id"], current_step="not_started", data={}, completed=False
            )

            # Clear Redis cache
            onboarding_redis.delete_progress(user["id"])

            logger.info(f"Reset onboarding progress for user {user['id']}")

            return reset_progress

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to reset progress: {str(e)}")
            raise DatabaseError(f"Failed to reset progress: {str(e)}")
