#!/usr/bin/env python
"""
Script to test the actual API endpoint for role matching.
"""

import os
import sys
import django
from pathlib import Path
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import AnonymousUser
from authentication.views.v1.role_views import JobInputView
from unittest.mock import Mock
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_job_input_endpoint():
    """Test the JobInputView endpoint with real data."""
    print("🧪 Testing JobInputView API Endpoint")
    print("=" * 50)
    
    try:
        # Create a DRF API request factory 
        factory = APIRequestFactory()
        
        # Test data - financial analyst role
        test_data = {
            'job_title': 'Financial Analyst',
            'job_description': 'I analyze financial data, create reports and provide investment recommendations. I work with Excel, SQL and financial modeling tools to support business decisions.'
        }
        
        print(f"\n📝 Test Data:")
        print(f"   Job Title: {test_data['job_title']}")
        print(f"   Job Description: {test_data['job_description'][:100]}...")
        
        # Create request
        request = factory.post(
            '/api/v1/role/job-input/',
            data=test_data,
            format='json'
        )
        
        # Mock authentication 
        class MockUser:
            def __init__(self):
                self.sub = 'auth0|683bd7b87653872d9ac747e1'  # Auth0 user ID
                self.email = 'test@example.com'
                self.is_authenticated = True
        
        request.user = MockUser()
        
        # Create DRF view properly
        view = JobInputView()
        view.request = request
        view.format_kwarg = None
        
        print(f"\n🔐 Using Auth0 ID: auth0|683bd7b87653872d9ac747e1")
        
        # Call the view
        print(f"\n🚀 Calling JobInputView endpoint...")
        response = view.post(request)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if hasattr(response, 'data'):
            response_data = response.data
        else:
            response_data = json.loads(response.content.decode('utf-8'))
        
        print(f"📄 Response Content:")
        
        if response.status_code == 200:
            print(f"   ✅ Success!")
            
            # Check user job input
            if 'user_job_input' in response_data:
                job_input = response_data['user_job_input']
                print(f"   📝 User Job Input:")
                print(f"      Title: {job_input.get('job_title')}")
                print(f"      Description: {job_input.get('job_description', '')[:80]}...")
                print(f"      Industry: {job_input.get('user_industry')}")
            
            # Check matched roles
            if 'matched_roles' in response_data:
                matched_roles = response_data['matched_roles']
                print(f"   🎯 Found {len(matched_roles)} matched roles:")
                
                for i, role in enumerate(matched_roles, 1):
                    print(f"      {i}. {role.get('title')} (Score: {role.get('relevance_score', 0):.3f})")
                    print(f"         Industry: {role.get('industry_name')}")
                    print(f"         ID: {role.get('id')}")
                    print(f"         Description: {role.get('description', '')[:80]}...")
                    
            print(f"   📈 Total Matches: {response_data.get('total_matches', 0)}")
            
        else:
            print(f"   ❌ Error Response:")
            print(f"      Status: {response.status_code}")
            print(f"      Content: {response_data}")
        
        # Test hotel manager role
        print(f"\n" + "="*50)
        print("🏨 Testing Hotel Manager Role")
        
        hotel_test_data = {
            'job_title': 'Hotel Manager',
            'job_description': 'I oversee daily hotel operations, manage staff, ensure guest satisfaction, and maintain quality standards across all departments.'
        }
        
        print(f"\n📝 Hotel Test Data:")
        print(f"   Job Title: {hotel_test_data['job_title']}")
        print(f"   Job Description: {hotel_test_data['job_description'][:100]}...")
        
        # Create request for hotel manager
        hotel_request = factory.post(
            '/api/v1/role/job-input/',
            data=hotel_test_data,
            format='json'
        )
        
        hotel_request.user = MockUser()
        
        # Call the view again
        hotel_view = JobInputView()
        hotel_view.request = hotel_request
        hotel_view.format_kwarg = None
        
        print(f"\n🚀 Calling JobInputView endpoint for hotel manager...")
        hotel_response = hotel_view.post(hotel_request)
        
        print(f"📊 Hotel Response Status: {hotel_response.status_code}")
        
        if hasattr(hotel_response, 'data'):
            hotel_response_data = hotel_response.data
        else:
            hotel_response_data = json.loads(hotel_response.content.decode('utf-8'))
        
        if hotel_response.status_code == 200:
            print(f"   ✅ Hotel search success!")
            
            if 'matched_roles' in hotel_response_data:
                hotel_matched_roles = hotel_response_data['matched_roles']
                print(f"   🎯 Found {len(hotel_matched_roles)} hotel matched roles:")
                
                for i, role in enumerate(hotel_matched_roles, 1):
                    print(f"      {i}. {role.get('title')} (Score: {role.get('relevance_score', 0):.3f})")
                    print(f"         Industry: {role.get('industry_name')}")
        else:
            print(f"   ❌ Hotel Error Response:")
            print(f"      Status: {hotel_response.status_code}")
            print(f"      Content: {hotel_response_data}")
        
        print(f"\n🎉 API endpoint testing completed!")
        
    except Exception as e:
        print(f"❌ Critical error during API testing: {str(e)}")
        logger.error(f"API testing failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_job_input_endpoint()