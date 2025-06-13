from typing import Dict, Any, List
from supabase import Client
from ...repositories.onboarding.job_roles_repository import JobRolesRepository
from ...integrations.openai import openai_client
from ...integrations.azure_search import azure_search_client
from ...core.logging import get_logger

logger = get_logger(__name__)

class AzureSearchService:
    """Service for managing Azure Search operations."""
    
    def __init__(self, db: Client):
        self.db = db
        self.job_roles_repo = JobRolesRepository(db)
    
    async def reindex_all_roles(self) -> Dict[str, Any]:
        """Reindex all roles in Azure Search."""
        try:
            # Get all roles with industry information
            logger.info("Fetching all roles for reindexing")
            roles = await self.job_roles_repo.get_all_roles_for_indexing()
            
            if not roles:
                return {
                    "success": True,
                    "message": "No roles to index",
                    "total_roles": 0,
                    "documents_indexed": 0
                }
            
            # Prepare documents for Azure Search
            documents = []
            for role in roles:
                if role.get("embedding_vector"):
                    # Create search keywords by combining title and industry
                    search_keywords = f"{role['title']} {role['industry_name']}"
                    
                    documents.append({
                        "id": role["id"],
                        "title": role["title"],
                        "description": role["description"],
                        "search_keywords": search_keywords,
                        "industry_id": role["industry_id"],
                        "industry_name": role["industry_name"],
                        "is_system_role": role["is_system_role"],
                        "embedding": role["embedding_vector"]
                    })
            
            # Clear existing index
            logger.info("Clearing existing index")
            await azure_search_client.delete_all_documents()
            
            # Upload documents in batches of 100
            batch_size = 100
            total_indexed = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await azure_search_client.upload_documents(batch)
                total_indexed += len(batch)
                logger.info(f"Indexed {total_indexed}/{len(documents)} documents")
            
            return {
                "success": True,
                "message": f"Successfully reindexed {total_indexed} roles",
                "total_roles": len(roles),
                "documents_indexed": total_indexed
            }
            
        except Exception as e:
            logger.error(f"Reindexing failed: {str(e)}")
            raise
    
    async def generate_missing_embeddings(self) -> Dict[str, Any]:
        """Generate embeddings for roles that don't have them."""
        try:
            # Get all roles
            logger.info("Fetching roles without embeddings")
            all_roles = await self.job_roles_repo.get_all()
            
            # Filter roles without embeddings
            roles_without_embeddings = [
                role for role in all_roles
                if not role.get("embedding_vector")
            ]
            
            if not roles_without_embeddings:
                return {
                    "success": True,
                    "message": "All roles already have embeddings",
                    "embeddings_generated": 0
                }
            
            # Generate embeddings
            embeddings_generated = 0
            for role in roles_without_embeddings:
                try:
                    # Combine title and description for embedding
                    text = f"Job Title: {role['title']}\n\nDescription: {role.get('description', '')}"
                    
                    # Generate embedding
                    embedding = await openai_client.generate_embedding(text)
                    
                    # Update role with embedding
                    await self.job_roles_repo.update(
                        role["id"],
                        {"embedding_vector": embedding}
                    )
                    
                    embeddings_generated += 1
                    logger.info(f"Generated embedding for role {role['id']} ({embeddings_generated}/{len(roles_without_embeddings)})")
                    
                except Exception as e:
                    logger.error(f"Failed to generate embedding for role {role['id']}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "message": f"Generated {embeddings_generated} embeddings",
                "embeddings_generated": embeddings_generated,
                "total_without_embeddings": len(roles_without_embeddings)
            }
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    async def clear_index(self) -> Dict[str, Any]:
        """Clear all documents from Azure Search index."""
        try:
            await azure_search_client.delete_all_documents()
            
            return {
                "success": True,
                "message": "Successfully cleared Azure Search index"
            }
            
        except Exception as e:
            logger.error(f"Index clearing failed: {str(e)}")
            raise