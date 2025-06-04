#!/usr/bin/env python
"""
Debug script to check actual search scores being returned.
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
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_search_scores():
    """Debug the actual search scores being returned."""
    print("🔍 Debugging Search Scores")
    print("=" * 50)
    
    try:
        role_manager = RoleManager()
        
        # Test Financial Analyst search
        financial_job_desc = JobDescription(
            title="Financial Analyst",
            description="I analyze financial data, create reports and provide investment recommendations. I work with Excel, SQL and financial modeling tools to support business decisions.",
            industry="Banking & Finance",
            hierarchy_level=HierarchyLevel.ASSOCIATE
        )
        
        print(f"\n📝 Test Query:")
        print(f"   Title: {financial_job_desc.title}")
        print(f"   Description: {financial_job_desc.description[:100]}...")
        print(f"   Search Text: {financial_job_desc.search_text[:120]}...")
        
        # Temporarily lower the threshold to see all results
        original_threshold = role_manager.MIN_RELEVANCY_SCORE
        role_manager.MIN_RELEVANCY_SCORE = 0.0  # Show all results for debugging
        
        print(f"\n🔍 Searching with threshold lowered to 0% (debugging)...")
        
        matches = role_manager.find_matching_roles(
            job_description=financial_job_desc,
            industry_filter="Banking & Finance",
            max_results=10
        )
        
        print(f"\n📊 Found {len(matches)} total matches:")
        for i, match in enumerate(matches, 1):
            print(f"   {i}. {match.role.title}")
            print(f"      Relevance Score: {match.relevance_score:.6f} ({match.relevance_score:.1%})")
            print(f"      Industry: {match.role.industry_name}")
            print(f"      Match Reasons: {', '.join(match.match_reasons)}")
            print()
        
        # Restore original threshold
        role_manager.MIN_RELEVANCY_SCORE = original_threshold
        
        print(f"🎯 With normal threshold ({original_threshold:.0%}):")
        matches_filtered = role_manager.find_matching_roles(
            job_description=financial_job_desc,
            industry_filter="Banking & Finance",
            max_results=10
        )
        
        print(f"   Filtered matches: {len(matches_filtered)}")
        for match in matches_filtered:
            print(f"   • {match.role.title}: {match.relevance_score:.1%}")
        
        # Test with a simpler query
        print(f"\n" + "="*50)
        print("🔍 Testing Simple Query")
        
        simple_job_desc = JobDescription(
            title="Financial Analyst",
            description="Financial analysis",
            industry="Banking & Finance",
            hierarchy_level=HierarchyLevel.ASSOCIATE
        )
        
        role_manager.MIN_RELEVANCY_SCORE = 0.0  # Show all results
        
        simple_matches = role_manager.find_matching_roles(
            job_description=simple_job_desc,
            industry_filter="Banking & Finance",
            max_results=10
        )
        
        print(f"\n📊 Simple query matches:")
        for i, match in enumerate(simple_matches, 1):
            print(f"   {i}. {match.role.title}: {match.relevance_score:.6f} ({match.relevance_score:.1%})")
        
        # Test direct Azure Search to see raw scores
        print(f"\n" + "="*50)
        print("🔧 Testing Direct Azure Search")
        
        try:
            from authentication.services.openai_service import OpenAIService
            openai_service = OpenAIService()
            
            # Generate embedding
            query_embedding = openai_service.get_embedding(financial_job_desc.search_text)
            
            # Direct Azure Search call
            search_result = role_manager.azure_search_service.hybrid_search_roles(
                text_query=f"{financial_job_desc.title} {financial_job_desc.description}",
                query_embedding=query_embedding,
                top_k=10,
                filters="industry_name eq 'Banking & Finance'"
            )
            
            if search_result['success']:
                print(f"\n📊 Direct Azure Search Results:")
                for i, result in enumerate(search_result['results'], 1):
                    print(f"   {i}. {result['title']}")
                    print(f"      Raw Score: {result.get('raw_score', 'N/A')}")
                    print(f"      Processed Score: {result['score']:.6f} ({result['score']:.1%})")
                    
        except Exception as e:
            print(f"   ❌ Direct Azure Search test failed: {str(e)}")
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        logger.error(f"Debug scoring failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    debug_search_scores()