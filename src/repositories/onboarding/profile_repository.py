from typing import Optional, Dict, Any
from supabase import Client
from ..base import SupabaseRepository
from ...models.enums import NativeLanguage


class ProfileRepository(SupabaseRepository):
    def __init__(self, db: Client):
        super().__init__(db, "users")
    
    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Auth0 ID."""
        return await self.get_by_field("auth0_id", auth0_id)
    
    async def update_native_language(self, user_id: str, native_language: NativeLanguage) -> Optional[Dict[str, Any]]:
        """Update user's native language."""
        data = {
            "native_language": native_language.value,
            "updated_at": "now()"
        }
        return await self.update(user_id, data)
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with onboarding-related fields."""
        result = self.db.table(self.table_name).select(
            "id, full_name, email, native_language, industry_id, selected_role_id, onboarding_status, hierarchy_level, created_at, updated_at"
        ).eq("id", user_id).execute()
        return result.data[0] if result.data else None