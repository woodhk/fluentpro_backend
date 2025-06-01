#!/usr/bin/env python3
"""
Test script to verify Azure AI Search functionality
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

from authentication.services.azure_search_service import AzureSearchService
from authentication.services.azure_openai_service import AzureOpenAIService


def test_azure_search():
    """
    Test Azure AI Search functionality with different search scenarios
    """
    print("🧪 Testing Azure AI Search functionality...")
    
    # Initialize services
    azure_search_service = AzureSearchService()
    azure_openai_service = AzureOpenAIService()
    
    try:
        # Test 1: Basic text search
        print("\n📊 Test 1: Basic text search for 'financial'")
        
        # Simple text search without vectors
        search_results = azure_search_service.search_client.search(
            search_text="financial",
            select=["id", "title", "description", "industry_name", "hierarchy_level"],
            top=3
        )
        
        results = list(search_results)
        print(f"   ✅ Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"   [{i}] {result['title']} ({result['industry_name']}) - Score: {result['@search.score']:.3f}")
        
        # Test 2: Vector similarity search
        print("\n🔍 Test 2: Vector similarity search")
        
        # Generate embedding for a test query
        test_query = "I work with financial data and create investment reports"
        test_embedding = azure_openai_service.get_embedding(test_query)
        
        print(f"   🔄 Generated query embedding: {len(test_embedding)} dimensions")
        
        # Perform vector search
        vector_result = azure_search_service.search_similar_roles(
            query_embedding=test_embedding,
            top_k=3
        )
        
        if vector_result['success']:
            print(f"   ✅ Vector search successful: {vector_result['total_results']} results")
            
            for i, result in enumerate(vector_result['results'], 1):
                print(f"   [{i}] {result['title']} ({result['industry_name']}) - Score: {result['score']:.3f}")
        else:
            print(f"   ❌ Vector search failed: {vector_result['error']}")
        
        # Test 3: Hybrid search (text + vector)
        print("\n🚀 Test 3: Hybrid search (text + vector)")
        
        hybrid_result = azure_search_service.hybrid_search_roles(
            text_query="data analyst",
            query_embedding=test_embedding,
            top_k=3
        )
        
        if hybrid_result['success']:
            print(f"   ✅ Hybrid search successful: {hybrid_result['total_results']} results")
            
            for i, result in enumerate(hybrid_result['results'], 1):
                print(f"   [{i}] {result['title']} ({result['industry_name']}) - Score: {result['score']:.3f}")
        else:
            print(f"   ❌ Hybrid search failed: {hybrid_result['error']}")
        
        # Test 4: Filtered search
        print("\n🎯 Test 4: Filtered search by hierarchy level")
        
        filtered_search = azure_search_service.search_client.search(
            search_text="manager",
            filter="hierarchy_level eq 'manager'",
            select=["id", "title", "hierarchy_level", "industry_name"],
            top=5
        )
        
        filtered_results = list(filtered_search)
        print(f"   ✅ Found {len(filtered_results)} manager-level roles")
        
        for i, result in enumerate(filtered_results, 1):
            print(f"   [{i}] {result['title']} ({result['hierarchy_level']}) - {result['industry_name']}")
        
        # Test 5: Industry-specific search
        print("\n🏢 Test 5: Industry-specific vector search")
        
        hotel_query = "I handle guest check-ins and provide customer service at the front desk"
        hotel_embedding = azure_openai_service.get_embedding(hotel_query)
        
        industry_result = azure_search_service.search_similar_roles(
            query_embedding=hotel_embedding,
            top_k=2,
            filters="industry_name eq 'Hotels & Hospitality'"
        )
        
        if industry_result['success']:
            print(f"   ✅ Industry-filtered search: {industry_result['total_results']} results")
            
            for i, result in enumerate(industry_result['results'], 1):
                print(f"   [{i}] {result['title']} ({result['industry_name']}) - Score: {result['score']:.3f}")
        else:
            print(f"   ❌ Industry-filtered search failed: {industry_result['error']}")
        
        # Final summary
        print(f"\n🎯 Test Summary:")
        print(f"   ✅ Text search: Working")
        print(f"   ✅ Vector similarity search: {vector_result['success']}")
        print(f"   ✅ Hybrid search: {hybrid_result['success']}")
        print(f"   ✅ Filtered search: Working")
        print(f"   ✅ Industry-specific search: {industry_result['success']}")
        
        all_tests_passed = (
            len(results) > 0 and
            vector_result['success'] and 
            hybrid_result['success'] and
            len(filtered_results) > 0 and
            industry_result['success']
        )
        
        if all_tests_passed:
            print(f"\n🎉 All tests passed! Azure AI Search is fully functional.")
            print(f"   🚀 Ready for Phase 2 role matching implementation!")
        else:
            print(f"\n⚠️  Some tests failed - check results above")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"💥 Test failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_azure_search()
    sys.exit(0 if success else 1)