#!/usr/bin/env python
"""
Debug script to test JobInputView functionality step by step.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

import logging
from unittest.mock import Mock, patch
from authentication.views.v1.role_views import JobInputView
from authentication.business.user_manager import UserManager
from authentication.business.role_manager import RoleManager
from authentication.models.role import JobDescription, RoleMatch, Role, HierarchyLevel
from authentication.models.user import UserProfile, OnboardingStatus, NativeLanguage
from core.responses import APIResponse

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_job_input_step_by_step():
    """Test each step of the job input process."""
    logger.info("=== Starting step-by-step JobInputView test ===")
    
    # Step 1: Test JobInputView initialization
    logger.info("Step 1: Testing JobInputView initialization")
    try:
        view = JobInputView()
        logger.info("✅ JobInputView initialized successfully")
    except Exception as e:
        logger.error(f"❌ JobInputView initialization failed: {e}")
        return False
    
    # Step 2: Test UserManager initialization
    logger.info("Step 2: Testing UserManager initialization")
    try:
        user_manager = UserManager()
        logger.info("✅ UserManager initialized successfully")
    except Exception as e:
        logger.error(f"❌ UserManager initialization failed: {e}")
        return False
    
    # Step 3: Test RoleManager initialization
    logger.info("Step 3: Testing RoleManager initialization")
    try:
        role_manager = RoleManager()
        logger.info("✅ RoleManager initialized successfully")
    except Exception as e:
        logger.error(f"❌ RoleManager initialization failed: {e}")
        return False
    
    # Step 4: Test JobDescription creation
    logger.info("Step 4: Testing JobDescription creation")
    try:
        job_description = JobDescription(
            title="Financial Analyst",
            description="Analyse financial data",
            industry="Technology"
        )
        logger.info(f"✅ JobDescription created: {job_description.search_text}")
    except Exception as e:
        logger.error(f"❌ JobDescription creation failed: {e}")
        return False
    
    # Step 5: Test individual service initialization
    logger.info("Step 5: Testing individual service initialization")
    try:
        from authentication.services.azure_openai_service import AzureOpenAIService
        azure_openai = AzureOpenAIService()
        logger.info("✅ AzureOpenAIService initialized successfully")
    except Exception as e:
        logger.error(f"❌ AzureOpenAIService initialization failed: {e}")
        return False
    
    try:
        from authentication.services.azure_search_service import AzureSearchService
        azure_search = AzureSearchService()
        logger.info("✅ AzureSearchService initialized successfully")
    except Exception as e:
        logger.error(f"❌ AzureSearchService initialization failed: {e}")
        return False
    
    try:
        from authentication.services.supabase_service import SupabaseService
        supabase = SupabaseService()
        logger.info("✅ SupabaseService initialized successfully")
    except Exception as e:
        logger.error(f"❌ SupabaseService initialization failed: {e}")
        return False
    
    # Step 6: Test embedding generation
    logger.info("Step 6: Testing embedding generation")
    try:
        test_text = "Financial Analyst Analyse financial data"
        embedding = azure_openai.generate_embedding(test_text)
        logger.info(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        return False
    
    # Step 7: Test role search functionality
    logger.info("Step 7: Testing role search functionality")
    try:
        # Mock the Azure Search call since we don't have real data
        with patch.object(azure_search, 'hybrid_search_roles') as mock_search:
            mock_search.return_value = {
                'success': True,
                'results': [
                    {
                        'id': 'test-role-1',
                        'title': 'Financial Analyst',
                        'description': 'Analyze financial data and create reports',
                        'industry_id': 'tech-industry',
                        'industry_name': 'Technology',
                        'hierarchy_level': 'associate',
                        'search_keywords': 'finance, analysis, data',
                        'score': 0.85,
                        'semantic_caption': []
                    }
                ]
            }
            
            matched_roles = role_manager.find_matching_roles(
                job_description=job_description,
                industry_filter="Technology",
                max_results=5
            )
            logger.info(f"✅ Role matching completed: {len(matched_roles)} roles found")
            
            # Test role match formatting
            if matched_roles:
                role_match = matched_roles[0]
                logger.info(f"✅ First role: {role_match.role.title}, score: {role_match.relevance_score}")
            
    except Exception as e:
        logger.error(f"❌ Role search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    logger.info("=== All tests completed successfully ===")
    return True

def test_mock_request():
    """Test with a mock request object."""
    logger.info("=== Testing with mock request ===")
    
    try:
        # Create mock request
        mock_request = Mock()
        mock_request.data = {
            'job_title': 'Financial Analyst',
            'job_description': 'Analyse financial data'
        }
        
        # Create view instance
        view = JobInputView()
        
        # Mock the authentication method
        view.get_auth0_user_id = Mock(return_value='auth0|683f02200de56388cf6c8db3')
        
        # Mock user profile
        mock_user_profile = Mock()
        mock_user_profile.industry_name = 'Technology'
        
        with patch.object(UserManager, 'get_user_profile', return_value=mock_user_profile):
            with patch.object(RoleManager, 'find_matching_roles', return_value=[]):
                response = view.post(mock_request)
                logger.info(f"✅ Mock request processed successfully")
                logger.info(f"Response type: {type(response)}")
                
    except Exception as e:
        logger.error(f"❌ Mock request failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_job_input_step_by_step()
    if success:
        success = test_mock_request()
    
    if success:
        logger.info("🎉 All tests passed!")
    else:
        logger.error("💥 Some tests failed!")
        sys.exit(1)