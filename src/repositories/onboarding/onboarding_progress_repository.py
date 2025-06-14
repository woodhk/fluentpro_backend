from typing import Optional, Dict, Any
from supabase import Client
from ..base import SupabaseRepository
from ...core.logging import get_logger

logger = get_logger(__name__)


class OnboardingProgressRepository(SupabaseRepository):
    """Repository for user onboarding progress operations."""

    def __init__(self, db: Client):
        super().__init__(db, "user_onboarding_progress")

    async def get_user_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding progress for a user."""
        try:
            result = (
                self.db.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user progress: {str(e)}")
            return None

    async def upsert_progress(
        self,
        user_id: str,
        current_step: str,
        data: Dict[str, Any],
        completed: bool = False,
    ) -> Dict[str, Any]:
        """Create or update user's onboarding progress."""
        progress_data = {
            "user_id": user_id,
            "current_step": current_step,
            "data": data,
            "completed": completed,
        }

        try:
            # Supabase Python client's upsert with on_conflict
            result = (
                self.db.table(self.table_name)
                .upsert(progress_data, on_conflict="user_id")
                .execute()
            )

            if not result.data:
                raise Exception("Failed to upsert onboarding progress")

            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to upsert progress: {str(e)}")
            raise

    async def mark_completed(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Mark onboarding as completed for a user."""
        try:
            result = (
                self.db.table(self.table_name)
                .update(
                    {
                        "current_step": "completed",
                        "completed": True,
                        "updated_at": "now()",
                    }
                )
                .eq("user_id", user_id)
                .execute()
            )

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to mark completed: {str(e)}")
            return None
