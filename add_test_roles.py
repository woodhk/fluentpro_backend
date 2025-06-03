#!/usr/bin/env python
"""
Script to add test role data to Azure Search index.
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

from authentication.services.azure_search_service import AzureSearchService
import uuid

def add_test_roles():
    """Add some test roles to the Azure Search index."""
    print("Adding test roles to Azure Search index...")
    
    azure_search = AzureSearchService()
    
    # Create test roles for Banking & Finance industry
    test_roles = [
        {
            'id': str(uuid.uuid4()),
            'title': 'Financial Analyst',
            'description': 'Analyze financial data, prepare reports, and support investment decisions. Work with Excel, SQL, and financial modeling tools.',
            'industry_id': '94642aff-7100-431b-a6a8-7fd741064a73',
            'industry_name': 'Banking & Finance',
            'hierarchy_level': 'associate',
            'search_keywords': ['financial', 'analyst', 'excel', 'modeling', 'reports', 'data analysis'],
            'is_active': True,
            'created_at': '2025-06-03T17:00:00Z'
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Senior Financial Analyst',
            'description': 'Lead financial analysis projects, mentor junior analysts, and provide strategic insights. Advanced Excel and financial modeling expertise required.',
            'industry_id': '94642aff-7100-431b-a6a8-7fd741064a73',
            'industry_name': 'Banking & Finance',
            'hierarchy_level': 'supervisor',
            'search_keywords': ['senior', 'financial', 'analyst', 'excel', 'modeling', 'leadership', 'strategy'],
            'is_active': True,
            'created_at': '2025-06-03T17:00:00Z'
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Investment Banking Analyst',
            'description': 'Support M&A transactions, prepare pitch books, and conduct financial due diligence. Strong analytical and presentation skills required.',
            'industry_id': '94642aff-7100-431b-a6a8-7fd741064a73',
            'industry_name': 'Banking & Finance',
            'hierarchy_level': 'associate',
            'search_keywords': ['investment', 'banking', 'analyst', 'M&A', 'pitch', 'due diligence', 'financial'],
            'is_active': True,
            'created_at': '2025-06-03T17:00:00Z'
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Risk Analyst',
            'description': 'Assess and monitor financial risks, develop risk models, and prepare regulatory reports. Experience with risk management tools preferred.',
            'industry_id': '94642aff-7100-431b-a6a8-7fd741064a73',
            'industry_name': 'Banking & Finance',
            'hierarchy_level': 'associate',
            'search_keywords': ['risk', 'analyst', 'modeling', 'regulatory', 'compliance', 'financial'],
            'is_active': True,
            'created_at': '2025-06-03T17:00:00Z'
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Data Analyst',
            'description': 'Extract insights from financial data, create dashboards, and support business intelligence initiatives. SQL and Python skills required.',
            'industry_id': '94642aff-7100-431b-a6a8-7fd741064a73',
            'industry_name': 'Banking & Finance',
            'hierarchy_level': 'associate',
            'search_keywords': ['data', 'analyst', 'SQL', 'python', 'dashboard', 'business intelligence', 'financial'],
            'is_active': True,
            'created_at': '2025-06-03T17:00:00Z'
        }
    ]
    
    # First, try to create the index
    print("Creating Azure Search index...")
    index_result = azure_search.create_roles_index()
    print(f"Index creation result: {index_result}")
    
    # Upload the test roles
    print("Uploading test roles...")
    upload_result = azure_search.upload_roles_to_index(test_roles)
    print(f"Upload result: {upload_result}")
    
    print("✅ Test roles added successfully!")

if __name__ == "__main__":
    add_test_roles()