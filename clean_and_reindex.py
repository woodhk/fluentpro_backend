#!/usr/bin/env python
"""
Script to clean Azure AI Search index and reindex fresh data from Supabase.
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
    """Clean index and reindex fresh data."""
    print("🧹 Starting Azure AI Search clean and reindex process...")
    
    try:
        # Initialize services
        print("📡 Initializing services...")
        azure_search = AzureSearchService()
        supabase = SupabaseService()
        
        # Step 1: Delete existing index
        print("\n🗑️  Step 1: Deleting existing index...")
        delete_result = azure_search.delete_index()
        if delete_result['success']:
            print(f"   ✅ {delete_result['message']}")
        else:
            print(f"   ⚠️  Delete warning: {delete_result['error']}")
            print("   (This is normal if index doesn't exist)")
        
        # Step 2: Create fresh index
        print("\n🔧 Step 2: Creating fresh Azure AI Search index...")
        index_result = azure_search.create_roles_index()
        if index_result['success']:
            print(f"   ✅ {index_result['message']}")
        else:
            print(f"   ❌ Error creating index: {index_result['error']}")
            return
        
        # Step 3: Get current roles from Supabase
        print("\n📋 Step 3: Fetching current roles from Supabase...")
        try:
            roles_data = supabase.get_all_roles_with_industry()
        except Exception as e:
            print(f"   ❌ Error fetching roles: {str(e)}")
            return
        
        print(f"   📊 Found {len(roles_data)} current roles to index")
        
        if not roles_data:
            print("   ⚠️  No roles found to index")
            return
        
        # Show what roles we're indexing
        print("   📝 Roles to be indexed:")
        for i, role in enumerate(roles_data, 1):
            print(f"      {i}. {role['title']} ({role['industry_name']})")
        
        # Step 4: Upload fresh roles to Azure AI Search
        print("\n⬆️  Step 4: Uploading fresh roles to Azure AI Search...")
        upload_result = azure_search.upload_roles_to_index(roles_data)
        
        if upload_result['success']:
            print(f"   ✅ Successfully uploaded {upload_result['successful_uploads']}/{upload_result['total_documents']} roles")
            if upload_result['failed_uploads'] > 0:
                print(f"   ⚠️  {upload_result['failed_uploads']} roles failed to upload")
        else:
            print(f"   ❌ Upload failed: {upload_result['error']}")
            return
        
        print("\n🎉 Clean and reindex completed successfully!")
        print(f"📈 Summary:")
        print(f"   • Index recreated from scratch")
        print(f"   • Total roles processed: {len(roles_data)}")
        print(f"   • Successfully indexed: {upload_result['successful_uploads']}")
        print(f"   • Failed to index: {upload_result['failed_uploads']}")
        
        # Step 5: Test the clean search functionality
        print("\n🧪 Step 5: Testing clean search functionality...")
        test_clean_search(azure_search)
        
    except Exception as e:
        print(f"❌ Critical error during clean and reindex: {str(e)}")
        logger.error(f"Clean and reindex failed: {str(e)}", exc_info=True)

def test_clean_search(azure_search):
    """Test the search functionality with a sample query after clean reindex."""
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
            top_k=5,
            filters="industry_name eq 'Banking & Finance'"
        )
        
        if search_result['success']:
            results = search_result['results']
            print(f"   ✅ Clean search test successful - found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result['title']} (Score: {result['score']:.3f})")
                print(f"         Industry: {result['industry_name']}")
                print(f"         ID: {result['id']}")
                print(f"         Description: {result['description'][:80]}...")
        else:
            print(f"   ❌ Clean search test failed: {search_result['error']}")
            
    except Exception as e:
        print(f"   ⚠️  Clean search test failed: {str(e)}")

if __name__ == "__main__":
    main()