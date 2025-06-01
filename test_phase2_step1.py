#!/usr/bin/env python3
"""
Test script for Phase 2 Step 1: Amy Wang Role Selection Process
This script simulates Amy Wang inputting her job title and description,
getting role recommendations, selecting a role, and verifying the selection.
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


def test_phase2_step1():
    """
    Test Phase 2 Step 1: Role Selection Process for Amy Wang
    """
    print("🧪 Testing Phase 2 Step 1: Amy Wang Role Selection Process")
    print("=" * 60)
    
    # Amy Wang's Auth0 ID (from existing test data)
    AMY_AUTH0_ID = "auth0|683bd7b87653872d9ac747e1"
    
    # Amy Wang's job input data
    amy_job_data = {
        "job_title": "Financial Data Analyst",
        "job_description": "I analyze financial data, create investment reports, and provide insights for portfolio management. I work with financial databases, create dashboards, and present findings to senior management."
    }
    
    try:
        # Initialize services
        supabase_service = SupabaseService()
        azure_search_service = AzureSearchService()
        azure_openai_service = AzureOpenAIService()
        
        print("🔍 Step 1: Verify Amy Wang's existing profile...")
        
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
        
        print(f"\\n🎯 Step 2: Simulate Amy's job input...")
        print(f"   💼 Job Title: {amy_job_data['job_title']}")
        print(f"   📋 Job Description: {amy_job_data['job_description'][:100]}...")
        
        # Create comprehensive query text for embedding (same as in JobInputView)
        query_text = f"Job Title: {amy_job_data['job_title']}\\nIndustry: {amy_profile['industry_name']}\\nDescription: {amy_job_data['job_description']}"
        
        # Generate embedding for Amy's job input
        print("   🔄 Generating embedding for job description...")
        query_embedding = azure_openai_service.get_embedding(query_text)
        print(f"   ✅ Generated embedding: {len(query_embedding)} dimensions")
        
        # Search for similar roles with industry filter
        print(f"\\n🔍 Step 3: Searching for relevant roles in {amy_profile['industry_name']}...")
        
        industry_filter = f"industry_name eq '{amy_profile['industry_name']}'"
        
        # Use hybrid search combining text and vector similarity
        search_result = azure_search_service.hybrid_search_roles(
            text_query=f"{amy_job_data['job_title']} {amy_job_data['job_description']}",
            query_embedding=query_embedding,
            top_k=5,
            filters=industry_filter
        )
        
        if not search_result['success']:
            print(f"   ❌ Role search failed: {search_result['error']}")
            return False
        
        print(f"   ✅ Found {search_result['total_results']} matching roles")
        
        # Display the matched roles
        matched_roles = search_result['results']
        print(f"\\n📊 Step 4: Role recommendations for Amy:")
        
        for i, role in enumerate(matched_roles, 1):
            print(f"   [{i}] {role['title']} (Score: {role['score']:.3f})")
            print(f"       📝 {role['description'][:80]}...")
            print(f"       🏢 Industry: {role['industry_name']}")
            print(f"       📈 Level: {role['hierarchy_level']}")
            print()
        
        if not matched_roles:
            print("   ❌ No matching roles found")
            return False
        
        # Simulate Amy selecting the highest-scoring role
        selected_role = matched_roles[0]  # Amy selects the best match
        print(f"🎯 Step 5: Amy selects role: '{selected_role['title']}'")
        print(f"   📝 Role ID: {selected_role['id']}")
        print(f"   🎯 Relevance Score: {selected_role['score']:.3f}")
        
        # Update Amy's selected role in Supabase
        print(f"\\n💾 Step 6: Updating Amy's selected role in Supabase...")
        
        update_result = supabase_service.update_user_selected_role(
            auth0_id=AMY_AUTH0_ID,
            role_id=selected_role['id']
        )
        
        if not update_result['success']:
            print(f"   ❌ Failed to update role: {update_result['error']}")
            return False
        
        print(f"   ✅ Successfully updated selected role")
        print(f"   👤 User ID: {update_result['user_id']}")
        print(f"   🎯 Selected Role: {update_result['role_title']}")
        
        # Verify the update by fetching Amy's profile again
        print(f"\\n✅ Step 7: Verifying role selection...")
        
        updated_profile = supabase_service.get_user_full_profile(AMY_AUTH0_ID)
        
        if not updated_profile:
            print("   ❌ Could not retrieve updated profile")
            return False
        
        if updated_profile['selected_role_id'] != selected_role['id']:
            print("   ❌ Role ID mismatch in database")
            return False
        
        if updated_profile['role_title'] != selected_role['title']:
            print("   ❌ Role title mismatch in database")
            return False
        
        print("   ✅ Role selection verified in database")
        print(f"   📝 Amy's Selected Role: {updated_profile['role_title']}")
        print(f"   🆔 Role ID: {updated_profile['selected_role_id']}")
        
        # Final summary
        print(f"\\n🎉 Phase 2 Step 1 Test Summary:")
        print(f"   👤 User: {updated_profile['full_name']}")
        print(f"   🌐 Native Language: {updated_profile['native_language']}")
        print(f"   🏢 Industry: {updated_profile['industry_name']}")
        print(f"   💼 Job Input: {amy_job_data['job_title']}")
        print(f"   🎯 Selected Role: {updated_profile['role_title']}")
        print(f"   📊 Relevance Score: {selected_role['score']:.3f}")
        print(f"   📈 Total Matches Found: {len(matched_roles)}")
        
        print(f"\\n🚀 Phase 2 Step 1 completed successfully!")
        print(f"   ✅ Amy Wang has successfully selected her role")
        print(f"   ✅ Database updated with selected_role_id")
        print(f"   ✅ Ready to proceed to Phase 2 Step 2")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase2_step1()
    sys.exit(0 if success else 1)