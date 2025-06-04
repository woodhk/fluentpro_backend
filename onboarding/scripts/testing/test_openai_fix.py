#!/usr/bin/env python
"""
Test script to verify OpenAI service formatting fixes.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.openai_service import OpenAIService

def test_description_rewriting():
    """Test the improved description rewriting functionality."""
    print("🧪 Testing OpenAI Description Rewriting Fix")
    print("=" * 50)
    
    openai_service = OpenAIService()
    
    # Test case 1: Simple first-person description
    test_description_1 = "I analyze cryptocurrency markets, develop trading strategies, and execute digital asset transactions. I work with advanced charting tools and market indicators to identify profitable opportunities."
    
    print(f"\n📝 Test Case 1 - Crypto Trading Analyst:")
    print(f"   Original: {test_description_1}")
    
    rewritten_1 = openai_service.rewrite_job_description("Crypto Trading Analyst", test_description_1)
    
    print(f"   Rewritten: {rewritten_1}")
    print(f"   ✅ Contains markdown? {'**' in rewritten_1 or '#' in rewritten_1}")
    print(f"   ✅ Contains job title repetition? {'Crypto Trading Analyst' in rewritten_1}")
    print(f"   ✅ Contains 'Job Title:' or 'Description:'? {'Job Title:' in rewritten_1 or 'Description:' in rewritten_1}")
    
    # Test case 2: Financial analyst description
    test_description_2 = "I analyze financial data, create reports and provide investment recommendations. I work with Excel, SQL and financial modeling tools to support business decisions."
    
    print(f"\n📝 Test Case 2 - Financial Analyst:")
    print(f"   Original: {test_description_2}")
    
    rewritten_2 = openai_service.rewrite_job_description("Financial Analyst", test_description_2)
    
    print(f"   Rewritten: {rewritten_2}")
    print(f"   ✅ Contains markdown? {'**' in rewritten_2 or '#' in rewritten_2}")
    print(f"   ✅ Contains job title repetition? {'Financial Analyst' in rewritten_2}")
    print(f"   ✅ Contains 'Job Title:' or 'Description:'? {'Job Title:' in rewritten_2 or 'Description:' in rewritten_2}")
    
    # Test the cleaning function directly
    print(f"\n🧹 Testing Cleaning Function:")
    messy_description = """**Job Title: Test Role**

**Description:**
This role involves analyzing data and creating reports. Works with various tools and technologies."""
    
    cleaned = openai_service._clean_description_formatting(messy_description)
    print(f"   Messy: {messy_description}")
    print(f"   Cleaned: {cleaned}")
    print(f"   ✅ Successfully cleaned? {not ('**' in cleaned or 'Job Title:' in cleaned or 'Description:' in cleaned)}")

if __name__ == "__main__":
    test_description_rewriting()