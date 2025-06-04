#!/usr/bin/env python
"""
Script to test the role matching functionality and debug issues.
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
from authentication.models.role import JobDescription, HierarchyLevel
from authentication.services.azure_search_service import AzureSearchService
from authentication.services.openai_service import OpenAIService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_role_matching():
    """Test the role matching functionality."""
    print("🧪 Testing Role Matching Functionality")
    print("=" * 50)
    
    try:
        # Initialize services
        role_manager = RoleManager()
        azure_search = AzureSearchService()
        openai_service = OpenAIService()
        
        # Test 1: Test job description creation and search text
        print("\n📝 Test 1: Job Description Creation")
        job_desc = JobDescription(
            title="Financial Analyst",
            description="I analyze financial data, create reports and provide investment recommendations. I work with Excel, SQL and financial modeling tools to support business decisions.",
            industry="Banking & Finance",
            hierarchy_level=HierarchyLevel.ASSOCIATE
        )
        
        print(f"   Title: {job_desc.title}")
        print(f"   Description: {job_desc.description[:100]}...")
        print(f"   Industry: {job_desc.industry}")
        print(f"   Search Text: {job_desc.search_text[:150]}...")
        
        # Test 2: Test embedding generation
        print("\n🔢 Test 2: Embedding Generation")
        try:
            embedding = openai_service.get_embedding(job_desc.search_text)
            print(f"   ✅ Generated embedding with {len(embedding)} dimensions")
            print(f"   First 5 values: {embedding[:5]}")
        except Exception as e:
            print(f"   ❌ Failed to generate embedding: {str(e)}")
            return
        
        # Test 3: Test direct Azure Search
        print("\n🔍 Test 3: Direct Azure Search")
        try:
            search_result = azure_search.hybrid_search_roles(
                text_query=f"{job_desc.title} {job_desc.description}",
                query_embedding=embedding,
                top_k=5,
                filters="industry_name eq 'Banking & Finance'"
            )
            
            if search_result['success']:
                results = search_result['results']
                print(f"   ✅ Found {len(results)} direct search results")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. {result['title']} (Score: {result['score']:.3f})")
                    print(f"         Industry: {result['industry_name']}")
                    print(f"         ID: {result['id']}")
            else:
                print(f"   ❌ Direct search failed: {search_result['error']}")
        except Exception as e:
            print(f"   ❌ Direct search error: {str(e)}")
        
        # Test 4: Test role manager find_matching_roles
        print("\n🎯 Test 4: Role Manager Matching")
        try:
            role_matches = role_manager.find_matching_roles(
                job_description=job_desc,
                industry_filter="Banking & Finance",
                max_results=5
            )
            
            print(f"   ✅ Found {len(role_matches)} role matches")
            for i, match in enumerate(role_matches, 1):
                print(f"      {i}. {match.role.title} (Score: {match.relevance_score:.3f})")
                print(f"         Industry: {match.role.industry_name}")
                print(f"         ID: {match.role.id}")
                print(f"         Match Reasons: {match.match_reasons}")
                
        except Exception as e:
            print(f"   ❌ Role manager matching error: {str(e)}")
            logger.error(f"Role matching failed: {str(e)}", exc_info=True)
        
        # Test 5: Test without industry filter
        print("\n🌐 Test 5: Search Without Industry Filter")
        try:
            search_result_no_filter = azure_search.hybrid_search_roles(
                text_query=f"{job_desc.title} {job_desc.description}",
                query_embedding=embedding,
                top_k=5
            )
            
            if search_result_no_filter['success']:
                results = search_result_no_filter['results']
                print(f"   ✅ Found {len(results)} results without filter")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. {result['title']} (Score: {result['score']:.3f})")
                    print(f"         Industry: {result['industry_name']}")
            else:
                print(f"   ❌ Search without filter failed: {search_result_no_filter['error']}")
        except Exception as e:
            print(f"   ❌ Search without filter error: {str(e)}")
        
        # Test 6: Test different job description
        print("\n💼 Test 6: Different Job Description")
        hotel_job_desc = JobDescription(
            title="Hotel Manager",
            description="I oversee daily hotel operations, manage staff, ensure guest satisfaction, and maintain quality standards across all departments.",
            industry="Hotels & Hospitality",
            hierarchy_level=HierarchyLevel.MANAGER
        )
        
        try:
            hotel_embedding = openai_service.get_embedding(hotel_job_desc.search_text)
            hotel_search_result = azure_search.hybrid_search_roles(
                text_query=f"{hotel_job_desc.title} {hotel_job_desc.description}",
                query_embedding=hotel_embedding,
                top_k=5,
                filters="industry_name eq 'Hotels & Hospitality'"
            )
            
            if hotel_search_result['success']:
                results = hotel_search_result['results']
                print(f"   ✅ Found {len(results)} hotel management results")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. {result['title']} (Score: {result['score']:.3f})")
                    print(f"         Industry: {result['industry_name']}")
            else:
                print(f"   ❌ Hotel search failed: {hotel_search_result['error']}")
        except Exception as e:
            print(f"   ❌ Hotel search error: {str(e)}")
        
        print("\n🎉 Role matching tests completed!")
        
    except Exception as e:
        print(f"❌ Critical error during testing: {str(e)}")
        logger.error(f"Testing failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_role_matching()