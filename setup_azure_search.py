#!/usr/bin/env python3
"""
Script to set up Azure AI Search index and upload role embeddings
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.supabase_service import SupabaseService
from authentication.services.azure_search_service import AzureSearchService


def setup_azure_search():
    """
    Set up Azure AI Search index and upload role data
    """
    print("🔍 Setting up Azure AI Search for role embeddings...")
    
    # Initialize services
    supabase_service = SupabaseService()
    azure_search_service = AzureSearchService()
    
    try:
        # Step 1: Create the search index
        print("\n📊 Step 1: Creating Azure AI Search index...")
        
        index_result = azure_search_service.create_roles_index()
        
        if index_result['success']:
            print(f"   ✅ {index_result['message']}")
        else:
            print(f"   ❌ Failed to create index: {index_result['error']}")
            return False
        
        # Step 2: Get role data from Supabase
        print("\n📋 Step 2: Fetching role data from Supabase...")
        
        # Get all roles with their industry information (no embeddings needed from Supabase)
        roles_for_search = supabase_service.get_all_roles_with_industry()
        
        if not roles_for_search:
            print("   ❌ No role data found in Supabase")
            return False
        
        print(f"   ✅ Retrieved {len(roles_for_search)} roles from Supabase")
        
        # Step 3: Note about on-the-fly embedding generation
        print("\n🔧 Step 3: Ready for Azure AI Search with on-the-fly embedding generation...")
        print(f"   🚀 Embeddings will be generated in real-time during upload")
        print(f"   📊 {len(roles_for_search)} roles prepared for indexing")
        
        # Step 4: Upload to Azure AI Search with on-the-fly embedding generation
        print("\n📤 Step 4: Uploading roles to Azure AI Search with real-time embedding generation...")
        
        upload_result = azure_search_service.upload_roles_to_index(roles_for_search)
        
        if upload_result['success']:
            print(f"   ✅ {upload_result['message']}")
            print(f"   📈 Successful uploads: {upload_result['successful_uploads']}")
            print(f"   📉 Failed uploads: {upload_result['failed_uploads']}")
        else:
            print(f"   ❌ Upload failed: {upload_result['error']}")
            return False
        
        # Step 5: Summary
        print(f"\n🎯 Setup Summary:")
        print(f"   ✅ Azure AI Search index created: {azure_search_service.roles_index_name}")
        print(f"   ✅ {upload_result['successful_uploads']} roles indexed successfully")
        print(f"   ✅ Vector search enabled with 1536-dimensional embeddings")
        print(f"   ✅ Hybrid search (text + vector) configured")
        print(f"   ✅ Semantic search enabled for better relevance")
        
        print(f"\n🚀 Azure AI Search is ready for Phase 2 role matching!")
        
        return True
        
    except Exception as e:
        print(f"💥 Setup failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    success = setup_azure_search()
    sys.exit(0 if success else 1)