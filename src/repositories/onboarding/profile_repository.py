from typing import Optional, Dict, Any
from supabase import Client
from ..base import SupabaseRepository
from ...models.enums import NativeLanguage, Industry


class ProfileRepository(SupabaseRepository):
    def __init__(self, db: Client):
        super().__init__(db, "users")

    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Auth0 ID."""
        return await self.get_by_field("auth0_id", auth0_id)

    async def update_native_language(
        self, user_id: str, native_language: NativeLanguage
    ) -> Optional[Dict[str, Any]]:
        """Update user's native language."""
        data = {"native_language": native_language.value, "updated_at": "now()"}
        return await self.update(user_id, data)

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with onboarding-related fields."""
        result = (
            self.db.table(self.table_name)
            .select(
                "id, full_name, email, native_language, industry_id, selected_role_id, onboarding_status, hierarchy_level, created_at, updated_at"
            )
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_industry_id_by_name(self, industry: Industry) -> Optional[str]:
        """Get industry ID by matching industry enum to database name."""
        # Map enum values to database names
        industry_mapping = {
            Industry.BANKING_FINANCE: "Banking & Finance",
            Industry.SHIPPING_LOGISTICS: "Shipping & Logistics",
            Industry.REAL_ESTATE: "Real Estate",
            Industry.HOTELS_HOSPITALITY: "Hotels & Hospitality",
        }

        industry_name = industry_mapping.get(industry)
        if not industry_name:
            return None

        result = (
            self.db.table("industries")
            .select("id")
            .eq("name", industry_name)
            .eq("status", "available")
            .execute()
        )
        return result.data[0]["id"] if result.data else None

    async def update_industry(
        self, user_id: str, industry_id: str
    ) -> Optional[Dict[str, Any]]:
        """Update user's industry."""
        data = {"industry_id": industry_id, "updated_at": "now()"}
        return await self.update(user_id, data)
