from typing import List, Dict, Any
from supabase import Client
from ...repositories.onboarding.communication_repository import CommunicationRepository
from ...repositories.onboarding.profile_repository import ProfileRepository
from ...core.exceptions import DatabaseError
from ...core.logging import get_logger

logger = get_logger(__name__)


class CommunicationService:
    """Service for managing communication partner and situation selections."""

    def __init__(self, db: Client):
        self.comm_repo = CommunicationRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def get_available_partners(self) -> Dict[str, Any]:
        """Get all available communication partners."""
        try:
            partners = await self.comm_repo.get_all_active_partners()

            return {"partners": partners, "total": len(partners)}
        except Exception as e:
            logger.error(f"Failed to get communication partners: {str(e)}")
            raise DatabaseError("Failed to retrieve communication partners")

    async def select_communication_partners(
        self, auth0_id: str, partner_ids: List[str]
    ) -> Dict[str, Any]:
        """Save user's communication partner selections."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            # Resolve partner identifiers to UUIDs
            resolved_ids = await self.comm_repo.resolve_partner_identifiers(partner_ids)
            
            # Validate all identifiers were resolved
            if len(resolved_ids) != len(partner_ids):
                available_partners = await self.comm_repo.get_all_active_partners()
                available_identifiers = [p["identifier"] for p in available_partners]
                invalid_ids = [pid for pid in partner_ids if pid not in available_identifiers]
                raise ValueError(f"Invalid partner identifiers: {invalid_ids}")

            # Save selections using UUIDs
            selections = await self.comm_repo.save_user_partner_selections(
                user_id=user["id"], partner_ids=resolved_ids
            )

            logger.info(
                f"User {user['id']} selected {len(selections)} communication partners"
            )

            return {
                "success": True,
                "selected_count": len(selections),
                "partner_selections": selections,
            }

        except ValueError:
            # Re-raise ValueError as-is for validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to save partner selections: {str(e)}")
            raise DatabaseError(f"Failed to save partner selections: {str(e)}")

    async def get_situations_for_partner(
        self, auth0_id: str, partner_id: str
    ) -> Dict[str, Any]:
        """Get available situations and user's selections for a specific partner."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            # Get all available situations
            all_situations = await self.comm_repo.get_all_active_units()

            # Resolve partner identifier to UUID for database lookup
            partner = await self.comm_repo.get_partner_by_identifier(partner_id)
            if not partner:
                raise ValueError("Invalid partner identifier")
            
            partner_uuid = str(partner["id"])

            # Get user's selected situations for this partner
            selected = await self.comm_repo.get_user_situations_for_partner(
                user_id=user["id"], partner_id=partner_uuid
            )
            # Convert selected UUIDs back to identifiers
            selected_unit_ids = [s["unit_id"] for s in selected]
            selected_identifiers = []
            for situation in all_situations:
                if str(situation["id"]) in selected_unit_ids:
                    selected_identifiers.append(situation["identifier"])

            return {
                "partner_id": partner_id,  # Return original identifier
                "partner_name": partner["name"],
                "available_situations": all_situations,
                "selected_situations": selected_identifiers,
            }

        except Exception as e:
            logger.error(f"Failed to get situations: {str(e)}")
            raise DatabaseError(f"Failed to get situations: {str(e)}")

    async def select_situations_for_partner(
        self, auth0_id: str, partner_id: str, situation_ids: List[str]
    ) -> Dict[str, Any]:
        """Save user's situation selections for a specific partner."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            # Resolve partner identifier to UUID
            partner = await self.comm_repo.get_partner_by_identifier(partner_id)
            if not partner:
                raise ValueError("Invalid partner identifier")
            
            partner_uuid = str(partner["id"])

            # Resolve situation identifiers to UUIDs
            resolved_unit_ids = await self.comm_repo.resolve_unit_identifiers(situation_ids)
            
            # Validate all identifiers were resolved
            if len(resolved_unit_ids) != len(situation_ids):
                available_situations = await self.comm_repo.get_all_active_units()
                available_identifiers = [s["identifier"] for s in available_situations]
                invalid_ids = [sid for sid in situation_ids if sid not in available_identifiers]
                raise ValueError(f"Invalid situation identifiers: {invalid_ids}")

            # Save selections using UUIDs
            selections = await self.comm_repo.save_user_partner_situations(
                user_id=user["id"], partner_id=partner_uuid, unit_ids=resolved_unit_ids
            )

            logger.info(
                f"User {user['id']} selected {len(selections)} situations for partner {partner_id}"
            )

            return {
                "success": True,
                "partner_id": partner_id,  # Return original identifier
                "selected_count": len(selections),
                "situation_selections": selections,
            }

        except Exception as e:
            logger.error(f"Failed to save situation selections: {str(e)}")
            raise DatabaseError(f"Failed to save situation selections: {str(e)}")

    async def get_user_selections_summary(self, auth0_id: str) -> Dict[str, Any]:
        """Get summary of all user's selections."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            # Get complete selections
            selections = await self.comm_repo.get_user_complete_selections(user["id"])

            # Calculate totals
            total_partners = len(selections["partners"])
            total_situations = sum(len(p["situations"]) for p in selections["partners"])

            return {
                "total_partners_selected": total_partners,
                "total_situations_selected": total_situations,
                "selections": selections["partners"],
            }

        except Exception as e:
            logger.error(f"Failed to get selections summary: {str(e)}")
            raise DatabaseError(f"Failed to get selections summary: {str(e)}")

    async def complete_part_2(self, auth0_id: str) -> Dict[str, Any]:
        """Mark Part 2 as complete and update onboarding status."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            # Verify user has made selections
            summary = await self.get_user_selections_summary(auth0_id)
            if summary["total_partners_selected"] == 0:
                raise ValueError("No communication partners selected")

            # No longer update onboarding_status in users table
            # The progress tracking is now handled by the progress service

            logger.info(f"User {user['id']} completed Part 2 of onboarding")

            return {
                "success": True,
                "message": "Part 2 completed successfully",
                "next_step": "part_3",
            }

        except ValueError:
            # Re-raise ValueError as-is for validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to complete Part 2: {str(e)}")
            raise DatabaseError(f"Failed to complete Part 2: {str(e)}")
