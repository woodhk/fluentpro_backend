#!/usr/bin/env python
"""
Script to index all roles from Supabase into Azure AI Search.
This script ensures proper setup of the search index and indexes all roles.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.azure_search_service import AzureSearchService
from authentication.services.supabase_service import SupabaseService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to index all roles into Azure AI Search."""
    print("🚀 Starting Azure AI Search indexing process...")
    
    try:
        # Initialize services
        print("📡 Initializing services...")
        azure_search = AzureSearchService()
        supabase = SupabaseService()
        
        # Step 1: Create or update the search index
        print("\n🔧 Step 1: Creating/updating Azure AI Search index...")
        index_result = azure_search.create_roles_index()
        if index_result['success']:
            print(f"   ✅ {index_result['message']}")
        else:
            print(f"   ❌ Error creating index: {index_result['error']}")
            return
        
        # Step 2: Get all roles from Supabase
        print("\n📋 Step 2: Fetching roles from Supabase...")
        try:
            roles_data = supabase.get_all_roles_with_industry()
        except Exception as e:
            print(f"   ❌ Error fetching roles: {str(e)}")
            return
        print(f"   📊 Found {len(roles_data)} roles to index")
        
        if not roles_data:
            print("   ⚠️  No roles found to index")
            return
        
        # Step 3: Upload roles to Azure AI Search
        print("\n⬆️  Step 3: Uploading roles to Azure AI Search...")
        upload_result = azure_search.upload_roles_to_index(roles_data)
        
        if upload_result['success']:
            print(f"   ✅ Successfully uploaded {upload_result['successful_uploads']}/{upload_result['total_documents']} roles")
            if upload_result['failed_uploads'] > 0:
                print(f"   ⚠️  {upload_result['failed_uploads']} roles failed to upload")
        else:
            print(f"   ❌ Upload failed: {upload_result['error']}")
            return
        
        print("\n🎉 Azure AI Search indexing completed successfully!")
        print(f"📈 Summary:")
        print(f"   • Total roles processed: {len(roles_data)}")
        print(f"   • Successfully indexed: {upload_result['successful_uploads']}")
        print(f"   • Failed to index: {upload_result['failed_uploads']}")
        
        # Step 4: Test the search functionality
        print("\n🧪 Step 4: Testing search functionality...")
        test_search(azure_search)
        
    except Exception as e:
        print(f"❌ Critical error during indexing: {str(e)}")
        logger.error(f"Indexing failed: {str(e)}", exc_info=True)

def test_search(azure_search):
    """Test the search functionality with a sample query."""
    try:
        from authentication.services.openai_service import OpenAIService
        
        openai_service = OpenAIService()
        
        # Test query
        test_query = "financial analyst banking"
        print(f"   🔍 Testing search with query: '{test_query}'")
        
        # Generate embedding for test query
        test_embedding = openai_service.get_embedding(test_query)
        
        # Perform hybrid search
        search_result = azure_search.hybrid_search_roles(
            text_query=test_query,
            query_embedding=test_embedding,
            top_k=3,
            filters="industry_name eq 'Banking & Finance'"
        )
        
        if search_result['success']:
            results = search_result['results']
            print(f"   ✅ Search test successful - found {len(results)} results")
            
            for i, result in enumerate(results[:2], 1):
                print(f"      {i}. {result['title']} (Score: {result['score']:.3f})")
                print(f"         Industry: {result['industry_name']}")
                print(f"         Description: {result['description'][:100]}...")
        else:
            print(f"   ❌ Search test failed: {search_result['error']}")
            
    except Exception as e:
        print(f"   ⚠️  Search test failed: {str(e)}")

if __name__ == "__main__":
    main()