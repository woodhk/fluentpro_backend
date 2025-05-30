#!/usr/bin/env python
"""
Quick test script to verify API endpoints work correctly
Run with: python test_api.py
"""

import requests
import json
import sys
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your deployed URL
API_BASE = f"{BASE_URL}/api/v1/auth"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health/")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_signup():
    """Test user signup"""
    print("\nTesting signup...")
    
    # Test data
    signup_data = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "TestPass123!",
        "date_of_birth": "1990-01-01"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/signup/",
            json=signup_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print("✅ Signup successful")
            data = response.json()
            print(f"User ID: {data.get('user', {}).get('id')}")
            return data.get('access_token'), data.get('refresh_token')
        elif response.status_code == 409:
            print("⚠️ User already exists, trying login instead...")
            return test_login()
        else:
            print(f"❌ Signup failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return None, None

def test_login():
    """Test user login"""
    print("\nTesting login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Login successful")
            data = response.json()
            return data.get('access_token'), data.get('refresh_token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None, None

def test_profile(access_token):
    """Test user profile endpoint"""
    print("\nTesting profile...")
    
    if not access_token:
        print("❌ No access token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE}/profile/", headers=headers)
        
        if response.status_code == 200:
            print("✅ Profile fetch successful")
            print(f"Profile: {response.json()}")
            return True
        else:
            print(f"❌ Profile fetch failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return False

def test_refresh_token(refresh_token):
    """Test token refresh"""
    print("\nTesting token refresh...")
    
    if not refresh_token:
        print("❌ No refresh token available")
        return False
    
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/refresh/",
            json=refresh_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Token refresh successful")
            data = response.json()
            return data.get('access_token')
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting API tests...")
    print(f"Testing API at: {API_BASE}")
    
    # Test health check
    if not test_health_check():
        print("\n❌ Health check failed. Make sure the server is running.")
        sys.exit(1)
    
    # Test signup/login
    access_token, refresh_token = test_signup()
    
    if not access_token:
        print("\n❌ Authentication failed. Check your Auth0 configuration.")
        sys.exit(1)
    
    # Test profile
    test_profile(access_token)
    
    # Test token refresh
    new_access_token = test_refresh_token(refresh_token)
    
    print("\n🎉 All tests completed!")
    print("\nNote: If you see Auth0 errors, make sure you have:")
    print("1. Created an Auth0 application")
    print("2. Configured your .env file with Auth0 credentials")
    print("3. Set up Supabase database with the users table")

if __name__ == "__main__":
    main()