"""Service for managing onboarding summary and completion."""
from typing import Dict, Any, List, Optional
from supabase import Client
from ...repositories.onboarding.profile_repository import ProfileRepository
from ...repositories.onboarding.job_roles_repository import JobRolesRepository
from ...repositories.onboarding.communication_repository import CommunicationRepository
from ...core.exceptions import DatabaseError, UserNotFoundError
from ...core.logging import get_logger
from ...models.enums import OnboardingStatus, NativeLanguage

logger = get_logger(__name__)


class OnboardingSummaryService:
    """Service for managing onboarding summary and completion."""

    def __init__(self, db: Client):
        self.profile_repo = ProfileRepository(db)
        self.roles_repo = JobRolesRepository(db)
        self.comm_repo = CommunicationRepository(db)
        self.db = db

    async def get_onboarding_summary(self, auth0_id: str) -> Dict[str, Any]:
        """Get complete onboarding summary for a user."""
        try:
            # Get user profile
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise UserNotFoundError("User not found")

            # Get native language display name
            native_language_display = self._get_language_display_name(
                user.get("native_language")
            )

            # Get industry details
            industry = await self._get_industry_details(user.get("industry_id"))

            # Get role details
            role_summary = await self._get_role_summary(
                user.get("selected_role_id"),
                user.get("custom_role_title"),
                user.get("custom_role_description"),
                industry["name"] if industry else "Unknown",
            )

            # Get communication preferences
            comm_summary = await self._get_communication_summary(user["id"])

            # Build summary
            summary = {
                "native_language": user.get("native_language"),
                "native_language_display": native_language_display,
                "industry_id": user.get("industry_id"),
                "industry_name": industry["name"] if industry else "Not selected",
                "role": role_summary,
                "communication_partners": comm_summary["partners"],
                "total_partners": comm_summary["total_partners"],
                "total_situations": comm_summary["total_situations"],
                "onboarding_status": user.get(
                    "onboarding_status", OnboardingStatus.PENDING.value
                ),
                "is_complete": user.get("onboarding_status")
                == OnboardingStatus.COMPLETED.value,
            }

            return summary

        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get onboarding summary: {str(e)}")
            raise DatabaseError(f"Failed to retrieve onboarding summary: {str(e)}")

    async def complete_onboarding(self, auth0_id: str) -> Dict[str, Any]:
        """Mark onboarding as complete."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise UserNotFoundError("User not found")

            # Verify all required fields are set
            validation_errors = self._validate_onboarding_completion(user)
            if validation_errors:
                raise ValueError(
                    f"Onboarding incomplete: {', '.join(validation_errors)}"
                )

            # No longer update onboarding_status in users table
            # The completion is tracked in the progress service

            logger.info(f"User {user['id']} completed onboarding")

            return {
                "success": True,
                "message": "Onboarding completed successfully!",
                "onboarding_status": OnboardingStatus.COMPLETED.value,
                "next_steps": "You can now access your personalized learning content.",
            }

        except (ValueError, UserNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to complete onboarding: {str(e)}")
            raise DatabaseError(f"Failed to complete onboarding: {str(e)}")

    def _get_language_display_name(self, language_code: Optional[str]) -> str:
        """Get display name for language code."""
        if not language_code:
            return "Not selected"

        language_map = {
            NativeLanguage.ENGLISH.value: "English",
            NativeLanguage.CHINESE_TRADITIONAL.value: "Traditional Chinese",
            NativeLanguage.CHINESE_SIMPLIFIED.value: "Simplified Chinese",
        }
        return language_map.get(language_code, "Unknown")

    async def _get_industry_details(
        self, industry_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get industry details by ID."""
        if not industry_id:
            return None

        try:
            result = (
                self.db.table("industries")
                .select("id, name")
                .eq("id", industry_id)
                .execute()
            )

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get industry details: {str(e)}")
            return None

    async def _get_role_summary(
        self,
        role_id: Optional[str],
        custom_title: Optional[str],
        custom_description: Optional[str],
        industry_name: str,
    ) -> Dict[str, Any]:
        """Get role summary details."""
        if custom_title and custom_description:
            # User created a custom role
            return {
                "id": role_id,
                "title": custom_title,
                "description": custom_description,
                "is_custom": True,
                "industry_name": industry_name,
            }
        elif role_id:
            # User selected a predefined role
            try:
                role = await self.roles_repo.get_by_id(role_id)
                if role:
                    return {
                        "id": role["id"],
                        "title": role["title"],
                        "description": role["description"],
                        "is_custom": False,
                        "industry_name": industry_name,
                    }
            except Exception as e:
                logger.error(f"Failed to get role details: {str(e)}")

        return {
            "id": None,
            "title": "No role selected",
            "description": "Please complete role selection",
            "is_custom": False,
            "industry_name": industry_name,
        }

    async def _get_communication_summary(self, user_id: str) -> Dict[str, Any]:
        """Get communication partners and situations summary."""
        try:
            # Get selected partners
            partners = await self.comm_repo.get_user_selected_partners(user_id)

            partner_summaries = []
            total_situations = 0

            for partner in partners:
                partner_id = partner["communication_partner_id"]

                # Get situations for this partner
                situations = await self.comm_repo.get_user_situations_for_partner(
                    user_id, partner_id
                )

                situation_summaries = []
                for sit in situations:
                    if sit.get("units"):
                        situation_summaries.append(
                            {
                                "id": sit["unit_id"],
                                "name": sit["units"]["name"],
                                "description": sit["units"].get("description"),
                                "priority": sit["priority"],
                            }
                        )
                        total_situations += 1

                if partner.get("communication_partners"):
                    partner_summaries.append(
                        {
                            "id": partner_id,
                            "name": partner["communication_partners"]["name"],
                            "description": partner["communication_partners"].get(
                                "description"
                            ),
                            "priority": partner["priority"],
                            "situations": situation_summaries,
                        }
                    )

            return {
                "partners": partner_summaries,
                "total_partners": len(partner_summaries),
                "total_situations": total_situations,
            }
        except Exception as e:
            logger.error(f"Failed to get communication summary: {str(e)}")
            return {"partners": [], "total_partners": 0, "total_situations": 0}

    def _validate_onboarding_completion(self, user: Dict[str, Any]) -> List[str]:
        """Validate that all required onboarding fields are complete."""
        errors = []

        if not user.get("native_language"):
            errors.append("Native language not selected")

        if not user.get("industry_id"):
            errors.append("Industry not selected")

        if not user.get("selected_role_id") and not (
            user.get("custom_role_title") and user.get("custom_role_description")
        ):
            errors.append("Role not selected")

        # Note: Communication partners are optional but recommended
        # You might want to add a check here if they become required

        return errors
