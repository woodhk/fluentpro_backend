from typing import Dict, Any, List, Optional
from supabase import Client
from ...repositories.onboarding.job_roles_repository import JobRolesRepository
from ...repositories.onboarding.profile_repository import ProfileRepository
from ...integrations.openai import openai_client
from ...integrations.azure_search import azure_search_client
from ...core.exceptions import DatabaseError
from ...core.logging import get_logger
from ...utils.validators import sanitize_string

logger = get_logger(__name__)


class JobMatchingService:
    def __init__(self, db: Client):
        self.job_roles_repo = JobRolesRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def search_roles(
        self, auth0_id: str, job_title: str, job_description: str
    ) -> Dict[str, Any]:
        """Search for matching roles based on user input."""
        try:
            # Get user profile to retrieve industry
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user or not user.get("industry_id"):
                raise DatabaseError("User industry not set")

            # Sanitize inputs
            job_title = sanitize_string(job_title, max_length=200)
            job_description = sanitize_string(job_description, max_length=1000)

            # Combine title and description for embedding
            combined_text = f"Job Title: {job_title}\n\nDescription: {job_description}"

            # Generate embedding
            logger.info(f"Generating embedding for user {user['id']}")
            embedding = await openai_client.generate_embedding(combined_text)

            # Search Azure for similar roles
            logger.info(f"Searching roles for industry {user['industry_id']}")
            matches = await azure_search_client.search_roles(
                embedding=embedding, industry_id=user["industry_id"], top_k=5
            )

            logger.info(f"Found {len(matches)} matches for user {user['id']}")

            return {
                "matches": matches,
                "search_metadata": {
                    "user_id": user["id"],
                    "industry_id": user["industry_id"],
                    "query_title": job_title,
                    "query_description": job_description,
                },
            }

        except Exception as e:
            logger.error(f"Role search failed: {str(e)}")
            raise DatabaseError(f"Failed to search roles: {str(e)}")

    async def select_role(
        self,
        auth0_id: str,
        role_id: Optional[str],
        custom_title: Optional[str] = None,
        custom_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle user's role selection or custom role creation."""
        try:
            # Get user
            user = await self.profile_repo.get_user_by_auth0_id(auth0_id)
            if not user:
                raise DatabaseError("User not found")

            if role_id:
                # User selected an existing role
                await self.job_roles_repo.update_user_selected_role(
                    user_id=user["id"], role_id=role_id
                )

                return {
                    "success": True,
                    "message": "Role selected successfully",
                    "role_id": role_id,
                    "is_custom": False,
                }

            elif custom_title and custom_description:
                # User submitted a custom role
                custom_title = sanitize_string(custom_title, max_length=200)
                custom_description = sanitize_string(
                    custom_description, max_length=1000
                )

                # Generate embedding for custom role
                combined_text = (
                    f"Job Title: {custom_title}\n\nDescription: {custom_description}"
                )
                embedding = await openai_client.generate_embedding(combined_text)

                # Create custom role
                custom_role = await self.job_roles_repo.create_custom_role(
                    title=custom_title,
                    description=custom_description,
                    industry_id=user["industry_id"],
                    embedding=embedding,
                )

                # Update user with custom role
                await self.job_roles_repo.update_user_selected_role(
                    user_id=user["id"],
                    role_id=custom_role["id"],
                    custom_title=custom_title,
                    custom_description=custom_description,
                )

                # Index the new role in Azure Search
                await self._index_single_role(custom_role, user["industry_id"])

                return {
                    "success": True,
                    "message": "Custom role created successfully",
                    "role_id": custom_role["id"],
                    "is_custom": True,
                }

            else:
                raise ValueError(
                    "Either role_id or custom role details must be provided"
                )

        except Exception as e:
            logger.error(f"Role selection failed: {str(e)}")
            raise DatabaseError(f"Failed to select role: {str(e)}")

    async def _index_single_role(self, role: Dict[str, Any], industry_id: str):
        """Index a single role in Azure Search."""
        try:
            # Get industry name
            industry = (
                await self.profile_repo.db.table("industries")
                .select("name")
                .eq("id", industry_id)
                .execute()
            )
            industry_name = industry.data[0]["name"] if industry.data else "Unknown"

            document = {
                "id": role["id"],
                "title": role["title"],
                "description": role["description"],
                "industry_id": industry_id,
                "industry_name": industry_name,
                "is_system_role": role.get("is_system_role", False),
                "embedding": role["embedding_vector"],
            }

            await azure_search_client.upload_documents([document])
            logger.info(f"Indexed role {role['id']} in Azure Search")

        except Exception as e:
            logger.error(f"Failed to index role: {str(e)}")
            # Don't fail the whole operation if indexing fails
