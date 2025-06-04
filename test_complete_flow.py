#!/usr/bin/env python
"""
Script to test the complete role matching flow end-to-end.
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

from authentication.business.role_manager import RoleManager
from authentication.business.user_manager import UserManager
from authentication.models.role import JobDescription, HierarchyLevel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_role_matching_flow():
    """Test the complete role matching flow with real user data."""
    print("🎯 Testing Complete Role Matching Flow")
    print("=" * 60)
    
    try:
        # Use a real Auth0 ID from the database
        auth0_id = 'auth0|683bd7b87653872d9ac747e1'
        
        # Initialize managers
        user_manager = UserManager()
        role_manager = RoleManager()
        
        # Step 1: Get user profile
        print(f"\n👤 Step 1: Getting user profile for {auth0_id}")
        user_profile = user_manager.get_user_profile(auth0_id)
        
        if not user_profile:
            print(f"   ❌ User not found")
            return
        
        print(f"   ✅ User found:")
        print(f"      Name: {user_profile.user.full_name}")
        print(f"      Email: {user_profile.user.email}")
        print(f"      Industry: {user_profile.industry_name}")
        print(f"      Current Role: {user_profile.role_title or 'None'}")
        
        if not user_profile.industry_name:
            print(f"   ⚠️  User has no industry selected")
            return
        
        # Step 2: Test Financial Analyst role matching
        print(f"\n💼 Step 2: Testing Financial Analyst role matching")
        
        financial_job_desc = JobDescription(
            title="Financial Analyst",
            description="I analyze financial data, create reports and provide investment recommendations. I work with Excel, SQL and financial modeling tools to support business decisions.",
            industry=user_profile.industry_name,
            hierarchy_level=HierarchyLevel.ASSOCIATE
        )
        
        print(f"   Job Title: {financial_job_desc.title}")
        print(f"   Description: {financial_job_desc.description[:100]}...")
        print(f"   Industry Filter: {user_profile.industry_name}")
        print(f"   Search Text: {financial_job_desc.search_text[:120]}...")
        
        # Find matching roles
        try:
            financial_matches = role_manager.find_matching_roles(
                job_description=financial_job_desc,
                industry_filter=user_profile.industry_name,
                max_results=5
            )
            
            print(f"   ✅ Found {len(financial_matches)} matches:")
            for i, match in enumerate(financial_matches, 1):
                print(f"      {i}. {match.role.title} (Score: {match.relevance_score:.3f})")
                print(f"         ID: {match.role.id}")
                print(f"         Industry: {match.role.industry_name}")
                print(f"         Description: {match.role.description[:80]}...")
                if match.match_reasons:
                    print(f"         Reasons: {', '.join(match.match_reasons)}")
                print()
                
        except Exception as e:
            print(f"   ❌ Financial analyst matching failed: {str(e)}")
            logger.error(f"Financial analyst matching error: {str(e)}", exc_info=True)
        
        # Step 3: Test role selection
        if 'financial_matches' in locals() and financial_matches:
            print(f"\n✅ Step 3: Testing role selection")
            
            best_match = financial_matches[0]
            print(f"   Selecting best match: {best_match.role.title} (ID: {best_match.role.id})")
            
            try:
                selection_result = user_manager.update_selected_role(auth0_id, best_match.role.id)
                
                if selection_result.get('success', True):  # Some methods return dict, some return the object directly
                    print(f"   ✅ Role selection successful!")
                    print(f"      Selected Role: {selection_result.get('role_title', best_match.role.title)}")
                    
                    # Verify selection by getting updated profile
                    updated_profile = user_manager.get_user_profile(auth0_id)
                    print(f"      Updated Profile Role: {updated_profile.role_title}")
                else:
                    print(f"   ❌ Role selection failed: {selection_result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ Role selection error: {str(e)}")
                logger.error(f"Role selection error: {str(e)}", exc_info=True)
        
        # Step 4: Test custom role creation
        print(f"\n🆕 Step 4: Testing custom role creation")
        
        custom_job_desc = JobDescription(
            title="Crypto Trading Analyst",
            description="I analyze cryptocurrency markets, develop trading strategies, and execute digital asset transactions. I use advanced charting tools and market indicators to identify profitable opportunities.",
            industry=user_profile.industry_name,
            hierarchy_level=HierarchyLevel.ASSOCIATE
        )
        
        print(f"   Creating custom role: {custom_job_desc.title}")
        print(f"   Description: {custom_job_desc.description[:100]}...")
        
        try:
            custom_role = role_manager.create_custom_role(
                job_description=custom_job_desc,
                industry_id=user_profile.industry_id,
                created_by_user_id=user_profile.user.id
            )
            
            print(f"   ✅ Custom role created successfully!")
            print(f"      ID: {custom_role.id}")
            print(f"      Title: {custom_role.title}")
            print(f"      Description: {custom_role.description[:100]}...")
            print(f"      Generated Keywords: {custom_role.search_keywords}")
            
            # Test if the custom role was indexed in Azure Search
            print(f"\n🔍 Step 5: Testing if custom role was indexed")
            
            # Search for the newly created role
            search_matches = role_manager.find_matching_roles(
                job_description=custom_job_desc,
                industry_filter=user_profile.industry_name,
                max_results=5
            )
            
            custom_role_found = False
            for match in search_matches:
                if match.role.id == custom_role.id:
                    custom_role_found = True
                    print(f"   ✅ Custom role found in search results!")
                    print(f"      Score: {match.relevance_score:.3f}")
                    break
            
            if not custom_role_found:
                print(f"   ⚠️  Custom role not found in search results (may take a moment to index)")
                
        except Exception as e:
            print(f"   ❌ Custom role creation failed: {str(e)}")
            logger.error(f"Custom role creation error: {str(e)}", exc_info=True)
        
        print(f"\n🎉 Complete role matching flow test completed!")
        
    except Exception as e:
        print(f"❌ Critical error during complete flow testing: {str(e)}")
        logger.error(f"Complete flow testing failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_complete_role_matching_flow()