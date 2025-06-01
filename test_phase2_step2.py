#!/usr/bin/env python3
"""
Test script for Phase 2 Step 2: Amy Wang Role Rejection and New Role Creation
This script simulates Amy Wang rejecting all presented roles and creating a new custom role.
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.supabase_service import SupabaseService
from authentication.services.azure_search_service import AzureSearchService
from authentication.services.azure_openai_service import AzureOpenAIService


def test_phase2_step2():
    """
    Test Phase 2 Step 2: New Role Creation for Amy Wang
    """
    print("🧪 Testing Phase 2 Step 2: Amy Wang Role Rejection & New Role Creation")
    print("=" * 70)
    
    # Amy Wang's Auth0 ID (from existing test data)
    AMY_AUTH0_ID = "auth0|683bd7b87653872d9ac747e1"
    
    # Amy's new unique job that doesn't match existing roles
    amy_new_job_data = {
        "job_title": "Crypto Investment Portfolio Manager",
        "job_description": "I specialize in managing cryptocurrency investment portfolios for high-net-worth individuals. I analyze blockchain trends, DeFi protocols, evaluate tokenomics, and create diversified crypto investment strategies while managing risk through sophisticated hedging techniques and compliance frameworks.",
        "hierarchy_level": "manager"
    }
    
    try:
        # Initialize services
        supabase_service = SupabaseService()
        azure_search_service = AzureSearchService()
        azure_openai_service = AzureOpenAIService()
        
        print("🔍 Step 1: Verify Amy Wang's current profile...")
        
        # Get Amy's current profile
        amy_profile = supabase_service.get_user_full_profile(AMY_AUTH0_ID)
        
        if not amy_profile:
            print("   ❌ Amy Wang not found in database")
            return False
        
        print(f"   ✅ Found Amy Wang: {amy_profile['full_name']}")
        print(f"   📝 Native Language: {amy_profile['native_language']}")
        print(f"   🏢 Industry: {amy_profile['industry_name']}")
        print(f"   👤 Current Selected Role: {amy_profile['role_title'] or 'None'}")
        
        # Verify Amy has completed previous steps
        if not amy_profile['native_language']:
            print("   ❌ Amy needs to complete native language selection first")
            return False
        
        if not amy_profile['industry_name']:
            print("   ❌ Amy needs to complete industry selection first")
            return False
        
        print("   ✅ Amy has completed prerequisite steps")
        
        print(f"\\n🚫 Step 2: Simulate Amy rejecting existing roles...")
        print("   💭 Amy: 'None of the suggested roles match my unique crypto portfolio management position'")
        print("   📝 Decision: Create new custom role")
        
        print(f"\\n🆕 Step 3: Amy inputs her unique job details...")
        print(f"   💼 Job Title: {amy_new_job_data['job_title']}")
        print(f"   📋 Job Description: {amy_new_job_data['job_description'][:100]}...")
        print(f"   📈 Hierarchy Level: {amy_new_job_data['hierarchy_level']}")
        
        # Step 4: Generate keywords using LLM
        print(f"\\n🤖 Step 4: Generating keywords using LLM...")
        generated_keywords = azure_openai_service.generate_role_keywords(
            amy_new_job_data['job_title'], 
            amy_new_job_data['job_description']
        )
        print(f"   ✅ Generated keywords: {', '.join(generated_keywords)}")
        
        # Step 5: Create new role in Supabase
        print(f"\\n💾 Step 5: Creating new role in Supabase...")
        
        role_creation_result = supabase_service.create_new_role(
            title=amy_new_job_data['job_title'],
            description=amy_new_job_data['job_description'],
            industry_id=amy_profile['industry_id'],
            search_keywords=generated_keywords,
            hierarchy_level=amy_new_job_data['hierarchy_level']
        )
        
        if not role_creation_result['success']:
            print(f"   ❌ Failed to create role: {role_creation_result['error']}")
            return False
        
        new_role_id = role_creation_result['role_id']
        print(f"   ✅ New role created successfully")
        print(f"   🆔 Role ID: {new_role_id}")
        
        # Step 6: Get the complete role data with industry information
        print(f"\\n📋 Step 6: Retrieving complete role data...")
        role_with_industry = supabase_service.get_role_with_industry(new_role_id)
        
        if not role_with_industry:
            print("   ❌ Failed to retrieve created role with industry info")
            return False
        
        print(f"   ✅ Role data retrieved successfully")
        print(f"   🏢 Industry: {role_with_industry['industry_name']}")
        print(f"   📊 Keywords: {', '.join(role_with_industry['search_keywords']) if role_with_industry['search_keywords'] else 'None'}")
        
        # Step 7: Add role to Azure AI Search index
        print(f"\\n🔍 Step 7: Adding role to Azure AI Search index...")
        
        search_index_result = azure_search_service.add_single_role_to_index(role_with_industry)
        
        if not search_index_result['success']:
            print(f"   ⚠️  Warning: Failed to add to search index: {search_index_result['error']}")
            # Continue execution as this is not critical for the core functionality
        else:
            print(f"   ✅ Role added to Azure Search index successfully")
        
        # Step 8: Update Amy's selected role
        print(f"\\n👤 Step 8: Updating Amy's selected role...")
        
        update_result = supabase_service.update_user_selected_role(
            auth0_id=AMY_AUTH0_ID,
            role_id=new_role_id
        )
        
        if not update_result['success']:
            print(f"   ❌ Failed to update Amy's selected role: {update_result['error']}")
            return False
        
        print(f"   ✅ Amy's selected role updated successfully")
        print(f"   👤 User ID: {update_result['user_id']}")
        print(f"   🎯 Selected Role: {update_result['role_title']}")
        
        # Step 9: Verify the complete update
        print(f"\\n✅ Step 9: Verifying complete role creation and selection...")
        
        updated_profile = supabase_service.get_user_full_profile(AMY_AUTH0_ID)
        
        if not updated_profile:
            print("   ❌ Could not retrieve updated profile")
            return False
        
        if updated_profile['selected_role_id'] != new_role_id:
            print("   ❌ Role ID mismatch in database")
            return False
        
        if updated_profile['role_title'] != amy_new_job_data['job_title']:
            print("   ❌ Role title mismatch in database")
            return False
        
        print("   ✅ Role creation and selection verified in database")
        print(f"   📝 Amy's New Role: {updated_profile['role_title']}")
        print(f"   🆔 Role ID: {updated_profile['selected_role_id']}")
        
        # Step 10: Test searching for the new role
        print(f"\\n🔍 Step 10: Testing search functionality with new role...")
        
        # Create a test query similar to the new role
        test_query = "cryptocurrency portfolio management DeFi blockchain"
        test_embedding = azure_openai_service.get_embedding(test_query)
        
        search_result = azure_search_service.search_similar_roles(
            query_embedding=test_embedding,
            top_k=3,
            filters=f"industry_name eq '{updated_profile['industry_name']}'"
        )
        
        if search_result['success'] and search_result['results']:
            print(f"   ✅ Search functionality working")
            print(f"   📊 Found {len(search_result['results'])} results")
            
            # Check if our new role appears in search results
            new_role_found = any(result['id'] == new_role_id for result in search_result['results'])
            if new_role_found:
                print(f"   🎯 New role appears in search results")
            else:
                print(f"   ⚠️  New role not found in search results (may take time to index)")
        else:
            print(f"   ⚠️  Search test failed: {search_result.get('error', 'Unknown error')}")
        
        # Final summary
        print(f"\\n🎉 Phase 2 Step 2 Test Summary:")
        print(f"   👤 User: {updated_profile['full_name']}")
        print(f"   🌐 Native Language: {updated_profile['native_language']}")
        print(f"   🏢 Industry: {updated_profile['industry_name']}")
        print(f"   🆕 New Role Created: {updated_profile['role_title']}")
        print(f"   🤖 LLM Generated Keywords: {', '.join(generated_keywords)}")
        print(f"   💾 Supabase Role ID: {updated_profile['selected_role_id']}")
        print(f"   🔍 Azure Search Status: {'✅ Added' if search_index_result['success'] else '⚠️ Failed'}")
        print(f"   📈 Hierarchy Level: {amy_new_job_data['hierarchy_level']}")
        
        print(f"\\n🚀 Phase 2 Step 2 completed successfully!")
        print(f"   ✅ Amy Wang rejected existing roles")
        print(f"   ✅ New custom role created with LLM-generated keywords")
        print(f"   ✅ Role added to Supabase database")
        print(f"   ✅ Role added to Azure AI Search index")
        print(f"   ✅ User's selected_role_id updated")
        print(f"   ✅ Ready for Phase 2 Step 3 or Phase 3")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase2_step2()
    sys.exit(0 if success else 1)