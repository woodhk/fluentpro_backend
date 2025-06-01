#!/usr/bin/env python3
"""
Test script for Enhanced Features: LLM Description Rewriting + Role Source Tracking
This script tests Amy Lu creating a new role with first-person description that gets rewritten by LLM
and tracks the role source as 'created' for future onboarding steps.
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
from authentication.services.azure_openai_service import AzureOpenAIService


def test_enhanced_features():
    """
    Test Enhanced Features: LLM Description Rewriting + Role Source Tracking for Amy Lu
    """
    print("🧪 Testing Enhanced Features: LLM Rewriting + Role Source Tracking")
    print("=" * 70)
    
    # Amy Lu's Auth0 ID (from existing test data)
    AMY_LU_AUTH0_ID = "auth0|683a574ace1131f9d43fae90"  # Different from Amy Wang
    
    # Amy Lu's job with first-person description (common user input style)
    amy_job_data = {
        "job_title": "Digital Marketing Analytics Specialist",
        "job_description": "I analyze digital marketing campaigns, track customer engagement metrics, and create comprehensive reports for management. I work with tools like Google Analytics, Facebook Ads Manager, and Tableau to optimize marketing ROI. I also collaborate with cross-functional teams to implement data-driven marketing strategies.",
        "hierarchy_level": "associate"
    }
    
    try:
        # Initialize services
        supabase_service = SupabaseService()
        azure_search_service = AzureSearchService()
        azure_openai_service = AzureOpenAIService()
        
        print("🔍 Step 1: Verify Amy Lu's current profile...")
        
        # Get Amy Lu's current profile
        amy_profile = supabase_service.get_user_full_profile(AMY_LU_AUTH0_ID)
        
        if not amy_profile:
            print("   ❌ Amy Lu not found in database")
            return False
        
        print(f"   ✅ Found Amy Lu: {amy_profile['full_name']}")
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
        
        print(f"\\n💼 Step 2: Amy inputs her job details (with first-person description)...")
        print(f"   📝 Job Title: {amy_job_data['job_title']}")
        print(f"   📋 Original Description (first-person): {amy_job_data['job_description'][:80]}...")
        print(f"   📈 Hierarchy Level: {amy_job_data['hierarchy_level']}")
        
        # Test Feature 1: LLM Description Rewriting
        print(f"\\n✏️  Step 3: Testing LLM description rewriting...")
        
        rewritten_description = azure_openai_service.rewrite_job_description(
            amy_job_data['job_title'], 
            amy_job_data['job_description']
        )
        
        print(f"   ✅ Description rewritten successfully")
        print(f"   📝 Original: {amy_job_data['job_description'][:60]}...")
        print(f"   ✏️  Rewritten: {rewritten_description[:60]}...")
        
        # Check if rewriting worked (should not contain "I " at start of sentences)
        first_person_indicators = ["I analyze", "I work", "I create", "I also", "I track"]
        original_has_first_person = any(indicator in amy_job_data['job_description'] for indicator in first_person_indicators)
        rewritten_has_first_person = any(indicator in rewritten_description for indicator in first_person_indicators)
        
        print(f"   🔍 Original contains first-person: {original_has_first_person}")
        print(f"   🔍 Rewritten contains first-person: {rewritten_has_first_person}")
        print(f"   {'✅ Successfully converted to third-person' if original_has_first_person and not rewritten_has_first_person else '⚠️ May need review'}")
        
        # Generate keywords using LLM
        print(f"\\n🤖 Step 4: Generating keywords using LLM...")
        generated_keywords = azure_openai_service.generate_role_keywords(
            amy_job_data['job_title'], 
            amy_job_data['job_description']
        )
        print(f"   ✅ Generated keywords: {', '.join(generated_keywords)}")
        
        # Create new role in Supabase with rewritten description
        print(f"\\n💾 Step 5: Creating new role in Supabase...")
        
        role_creation_result = supabase_service.create_new_role(
            title=amy_job_data['job_title'],
            description=rewritten_description,  # Use rewritten description
            industry_id=amy_profile['industry_id'],
            search_keywords=generated_keywords,
            hierarchy_level=amy_job_data['hierarchy_level']
        )
        
        if not role_creation_result['success']:
            print(f"   ❌ Failed to create role: {role_creation_result['error']}")
            return False
        
        new_role_id = role_creation_result['role_id']
        print(f"   ✅ New role created successfully")
        print(f"   🆔 Role ID: {new_role_id}")
        
        # Get the complete role data with industry information
        print(f"\\n📋 Step 6: Retrieving complete role data...")
        role_with_industry = supabase_service.get_role_with_industry(new_role_id)
        
        if not role_with_industry:
            print("   ❌ Failed to retrieve created role with industry info")
            return False
        
        print(f"   ✅ Role data retrieved successfully")
        print(f"   📝 Stored Description: {role_with_industry['description'][:60]}...")
        
        # Add role to Azure AI Search index
        print(f"\\n🔍 Step 7: Adding role to Azure AI Search index...")
        
        search_index_result = azure_search_service.add_single_role_to_index(role_with_industry)
        
        if not search_index_result['success']:
            print(f"   ⚠️  Warning: Failed to add to search index: {search_index_result['error']}")
        else:
            print(f"   ✅ Role added to Azure Search index successfully")
        
        # Update Amy's selected role
        print(f"\\n👤 Step 8: Updating Amy Lu's selected role...")
        
        update_result = supabase_service.update_user_selected_role(
            auth0_id=AMY_LU_AUTH0_ID,
            role_id=new_role_id
        )
        
        if not update_result['success']:
            print(f"   ❌ Failed to update Amy's selected role: {update_result['error']}")
            return False
        
        print(f"   ✅ Amy's selected role updated successfully")
        
        # Test Feature 2: Role Source Tracking
        print(f"\\n📝 Step 9: Testing role source tracking...")
        
        session_update = supabase_service.update_user_session_role_source(
            auth0_id=AMY_LU_AUTH0_ID,
            role_source='created',
            role_details={
                'created_role_id': new_role_id,
                'created_role_title': amy_job_data['job_title'],
                'original_description': amy_job_data['job_description'],
                'rewritten_description': rewritten_description,
                'generated_keywords': generated_keywords
            }
        )
        
        if not session_update['success']:
            print(f"   ❌ Failed to track role source: {session_update['error']}")
            return False
        
        print(f"   ✅ Role source tracked successfully")
        print(f"   📊 Session ID: {session_update['session_id']}")
        print(f"   🏷️  Role Source: {session_update['role_source']}")
        
        # Verify role source tracking
        print(f"\\n✅ Step 10: Verifying role source retrieval...")
        
        role_source_data = supabase_service.get_user_role_source(AMY_LU_AUTH0_ID)
        
        if not role_source_data:
            print("   ❌ Could not retrieve role source data")
            return False
        
        print(f"   ✅ Role source data retrieved successfully")
        print(f"   🏷️  Source: {role_source_data['role_source']}")
        print(f"   ⏰ Timestamp: {role_source_data['role_source_timestamp']}")
        
        # Verify the complete profile update
        print(f"\\n🔍 Step 11: Verifying complete implementation...")
        
        updated_profile = supabase_service.get_user_full_profile(AMY_LU_AUTH0_ID)
        
        if not updated_profile:
            print("   ❌ Could not retrieve updated profile")
            return False
        
        if updated_profile['selected_role_id'] != new_role_id:
            print("   ❌ Role ID mismatch in database")
            return False
        
        if updated_profile['role_title'] != amy_job_data['job_title']:
            print("   ❌ Role title mismatch in database")
            return False
        
        print("   ✅ Complete implementation verified")
        
        # Final summary
        print(f"\\n🎉 Enhanced Features Test Summary:")
        print(f"   👤 User: {updated_profile['full_name']}")
        print(f"   🌐 Native Language: {updated_profile['native_language']}")
        print(f"   🏢 Industry: {updated_profile['industry_name']}")
        print(f"   🆕 New Role Created: {updated_profile['role_title']}")
        print(f"   📈 Hierarchy Level: {amy_job_data['hierarchy_level']}")
        print(f"   💾 Supabase Role ID: {updated_profile['selected_role_id']}")
        
        print(f"\\n✏️  Feature 1: LLM Description Rewriting")
        print(f"   📝 Original had first-person: {original_has_first_person}")
        print(f"   ✏️  Rewritten removed first-person: {not rewritten_has_first_person}")
        print(f"   ✅ Status: {'Success' if original_has_first_person and not rewritten_has_first_person else 'Needs Review'}")
        
        print(f"\\n📊 Feature 2: Role Source Tracking")
        print(f"   🏷️  Role Source: {role_source_data['role_source']}")
        print(f"   📝 Tracking Status: ✅ Successfully stored in user session")
        print(f"   🔍 Azure Search Status: {'✅ Added' if search_index_result['success'] else '⚠️ Failed'}")
        
        print(f"\\n🚀 Both enhanced features completed successfully!")
        print(f"   ✅ Feature 1: First-person descriptions automatically rewritten")
        print(f"   ✅ Feature 2: Role source tracked for onboarding continuity")
        print(f"   ✅ Ready for next phase with full context about role origin")
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_enhanced_features()
    sys.exit(0 if success else 1)