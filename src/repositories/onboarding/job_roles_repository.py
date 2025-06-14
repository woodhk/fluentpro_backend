from typing import Optional, Dict, Any, List
from supabase import Client
from ..base import SupabaseRepository
from ...core.logging import get_logger

logger = get_logger(__name__)


class JobRolesRepository(SupabaseRepository):
    def __init__(self, db: Client):
        super().__init__(db, "roles")

    async def get_roles_by_industry(self, industry_id: str) -> List[Dict[str, Any]]:
        """Get all roles for a specific industry."""
        return await self.get_many_by_field("industry_id", industry_id)

    async def create_custom_role(
        self, title: str, description: str, industry_id: str, embedding: List[float]
    ) -> Dict[str, Any]:
        """Create a custom user-submitted role."""
        data = {
            "title": title,
            "description": description,
            "industry_id": industry_id,
            "embedding_vector": embedding,
            "is_system_role": False,
        }
        return await self.create(data)

    async def get_all_roles_for_indexing(self) -> List[Dict[str, Any]]:
        """Get all roles with industry information for Azure indexing."""
        query = self.db.table(self.table_name).select(
            "id, title, description, industry_id, embedding_vector, is_system_role, industries!inner(id, name)"
        )
        result = query.execute()

        # Flatten the response
        roles = []
        for role in result.data:
            roles.append(
                {
                    "id": role["id"],
                    "title": role["title"],
                    "description": role["description"],
                    "industry_id": role["industry_id"],
                    "industry_name": role["industries"]["name"],
                    "embedding_vector": role["embedding_vector"],
                    "is_system_role": role["is_system_role"],
                }
            )

        return roles

    async def update_user_selected_role(
        self,
        user_id: str,
        role_id: Optional[str],
        custom_title: Optional[str] = None,
        custom_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update user's selected role or custom role."""
        data = {
            "selected_role_id": role_id,
            "custom_role_title": custom_title,
            "custom_role_description": custom_description,
            "updated_at": "now()",
        }

        result = self.db.table("users").update(data).eq("id", user_id).execute()
        return result.data[0] if result.data else None
