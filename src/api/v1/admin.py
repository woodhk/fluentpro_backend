from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Annotated
from supabase import Client
from ...core.dependencies import get_current_user, get_db
from ...core.rate_limiting import limiter, STRICT_RATE_LIMIT
from ...services.onboarding.azure_search_service import AzureSearchService
from ...core.logging import get_logger

router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


@router.post("/reindex-roles")
@limiter.limit(STRICT_RATE_LIMIT)
async def reindex_all_roles(
    request: Request,
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    """Reindex all roles in Azure Search (Admin only)."""
    # TODO: Add proper admin role check when user roles are implemented
    # For now, any authenticated user can access

    logger.info(f"User {current_user['id']} initiated role reindexing")

    azure_search_service = AzureSearchService(db)

    try:
        result = await azure_search_service.reindex_all_roles()
        return result
    except Exception as e:
        logger.error(f"Reindexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-embeddings")
@limiter.limit(STRICT_RATE_LIMIT)
async def generate_missing_embeddings(
    request: Request,
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    """Generate embeddings for roles that don't have them (Admin only)."""
    logger.info(f"User {current_user['id']} initiated embedding generation")

    azure_search_service = AzureSearchService(db)

    try:
        result = await azure_search_service.generate_missing_embeddings()
        return result
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-index")
@limiter.limit(STRICT_RATE_LIMIT)
async def clear_search_index(
    request: Request,
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[Client, Depends(get_db)],
):
    """Clear all documents from Azure Search index (Admin only)."""
    logger.warning(f"User {current_user['id']} initiated index clearing")

    azure_search_service = AzureSearchService(db)

    try:
        result = await azure_search_service.clear_index()
        return result
    except Exception as e:
        logger.error(f"Index clearing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
