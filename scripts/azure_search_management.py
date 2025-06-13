#!/usr/bin/env python3
"""
Azure Search Management Script
Usage: python scripts/azure_search_management.py [command]

Commands:
  create-index    Create the Azure Search index
  reindex        Reindex all roles
  clear-index    Clear all documents from index
  generate-embeddings Generate missing embeddings
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_supabase_client
from src.integrations.azure_search import azure_search_client
from src.services.onboarding.azure_search_service import AzureSearchService
from src.core.logging import get_logger

logger = get_logger(__name__)

async def create_index():
    """Create the Azure Search index."""
    try:
        logger.info("Creating Azure Search index...")
        await azure_search_client.create_index()
        print("✅ Azure Search index created successfully")
    except Exception as e:
        print(f"❌ Failed to create index: {str(e)}")
        return 1
    return 0

async def reindex_roles():
    """Reindex all roles."""
    try:
        logger.info("Starting role reindexing...")
        db = get_supabase_client()
        service = AzureSearchService(db)
        result = await service.reindex_all_roles()
        
        print(f"✅ Reindexing complete:")
        print(f"   - Total roles: {result['total_roles']}")
        print(f"   - Documents indexed: {result['documents_indexed']}")
    except Exception as e:
        print(f"❌ Reindexing failed: {str(e)}")
        return 1
    return 0

async def clear_index():
    """Clear all documents from index."""
    try:
        # Confirm action
        response = input("⚠️  This will delete all documents from the index. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return 0
        
        logger.info("Clearing Azure Search index...")
        db = get_supabase_client()
        service = AzureSearchService(db)
        result = await service.clear_index()
        
        print("✅ Index cleared successfully")
    except Exception as e:
        print(f"❌ Failed to clear index: {str(e)}")
        return 1
    return 0

async def generate_embeddings():
    """Generate missing embeddings."""
    try:
        logger.info("Generating missing embeddings...")
        db = get_supabase_client()
        service = AzureSearchService(db)
        result = await service.generate_missing_embeddings()
        
        print(f"✅ Embedding generation complete:")
        print(f"   - Embeddings generated: {result['embeddings_generated']}")
        print(f"   - Total without embeddings: {result.get('total_without_embeddings', 0)}")
    except Exception as e:
        print(f"❌ Embedding generation failed: {str(e)}")
        return 1
    return 0

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    command = sys.argv[1]
    
    commands = {
        'create-index': create_index,
        'reindex': reindex_roles,
        'clear-index': clear_index,
        'generate-embeddings': generate_embeddings
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1
    
    return await commands[command]()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)