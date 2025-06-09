"""
Test suite for comprehensive user signup flow validation.

This test validates the complete signup process including:
- Auth0 user registration and verification
- Supabase user data storage with correct schema
- Proper onboarding_status initialization
- Authentication token generation and validation

Expected behavior based on legacy implementation (commit fede7002f840...):
- User should be created in Auth0 with provided credentials
- User data should be stored in Supabase with all required fields
- onboarding_status should be set to 'pending' (first step in onboarding flow)
- Response should include valid authentication tokens
"""

import pytest
import json
import logging
from datetime import date
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

# Configure detailed logging for test debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserSignupFlowTest(TestCase):
    """Comprehensive test for user signup flow."""
    
    def setUp(self):
        """Set up test environment with API client and test data."""
        self.client = APIClient()
        self.signup_url = '/api/v1/auth/users/signup/'
        
        # Test user data - real-world scenario
        self.test_user_data = {
            'full_name': 'John Alexander Smith',
            'email': 'john.smith.test@example.com',
            'password': 'SecurePassword123!',
            'password_confirmation': 'SecurePassword123!',
            'date_of_birth': '1990-05-15',
            'terms_accepted': True
        }
        
        logger.info("=== SIGNUP TEST SETUP COMPLETE ===")
        logger.info(f"Test user email: {self.test_user_data['email']}")
        logger.info(f"Test user DOB: {self.test_user_data['date_of_birth']}")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.create_user')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.create')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_complete_user_signup_flow(self, mock_get_by_email, mock_create_user_db, mock_create_auth0):
        """
        Test the complete user signup flow with all validations.
        
        This test verifies:
        1. Auth0 user creation with proper credentials
        2. Supabase database storage with correct schema
        3. Proper onboarding_status initialization to 'pending'
        4. Authentication response structure and token validity
        """
        logger.info("=== STARTING COMPREHENSIVE SIGNUP FLOW TEST ===")
        
        # Step 1: Mock Auth0 user creation
        logger.info("Step 1: Setting up Auth0 mock response")
        mock_auth0_user = {
            'user_id': 'auth0|abc123def456',
            'email': self.test_user_data['email'],
            'email_verified': True,
            'created_at': '2025-06-09T10:00:00.000Z'
        }
        mock_create_auth0.return_value = mock_auth0_user
        logger.info(f"Mock Auth0 user ID: {mock_auth0_user['user_id']}")
        
        # Step 2: Mock database operations
        logger.info("Step 2: Setting up Supabase mock responses")
        
        # Mock that user doesn't exist initially
        mock_get_by_email.return_value = None
        
        # Mock successful user creation in Supabase
        mock_db_user = {
            'id': 'user-uuid-123',
            'full_name': self.test_user_data['full_name'],
            'email': self.test_user_data['email'],
            'date_of_birth': self.test_user_data['date_of_birth'],
            'auth0_id': mock_auth0_user['user_id'],
            'is_active': True,
            'onboarding_status': 'pending',  # Critical: Should be set to first step
            'native_language': None,
            'industry_id': None,
            'selected_role_id': None,
            'hierarchy_level': None,
            'created_at': '2025-06-09T10:00:00.000Z',
            'updated_at': '2025-06-09T10:00:00.000Z'
        }
        mock_create_user_db.return_value = mock_db_user
        logger.info(f"Mock Supabase user ID: {mock_db_user['id']}")
        logger.info(f"Mock onboarding_status: {mock_db_user['onboarding_status']}")
        
        # Step 3: Execute signup request
        logger.info("Step 3: Making signup API request")
        logger.info(f"Request URL: {self.signup_url}")
        logger.info(f"Request data: {json.dumps(self.test_user_data, indent=2)}")
        
        response = self.client.post(
            self.signup_url,
            data=json.dumps(self.test_user_data),
            content_type='application/json'
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response data: {json.dumps(response.json() if response.content else {}, indent=2)}")
        
        # Step 4: Validate response structure and status
        logger.info("Step 4: Validating response structure")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response_data = response.json()
        self.assertIn('user', response_data)
        self.assertIn('tokens', response_data)
        
        # Step 5: Validate Auth0 integration
        logger.info("Step 5: Validating Auth0 integration")
        mock_create_auth0.assert_called_once()
        auth0_call_args = mock_create_auth0.call_args[1]
        
        # Verify Auth0 was called with correct user data
        self.assertEqual(auth0_call_args['email'], self.test_user_data['email'])
        self.assertEqual(auth0_call_args['password'], self.test_user_data['password'])
        self.assertEqual(auth0_call_args['name'], self.test_user_data['full_name'])
        logger.info("✓ Auth0 integration validated successfully")
        
        # Step 6: Validate Supabase database integration
        logger.info("Step 6: Validating Supabase database integration")
        mock_create_user_db.assert_called_once()
        db_call_args = mock_create_user_db.call_args[0][0]  # First positional argument
        
        # Critical validations for Supabase schema compliance
        self.assertEqual(db_call_args.full_name, self.test_user_data['full_name'])
        self.assertEqual(db_call_args.email, self.test_user_data['email'])
        self.assertEqual(str(db_call_args.date_of_birth), self.test_user_data['date_of_birth'])
        self.assertEqual(db_call_args.auth0_id, mock_auth0_user['user_id'])
        self.assertTrue(db_call_args.is_active)
        
        # Most critical: Verify onboarding_status is set to 'pending' (first step)
        self.assertEqual(db_call_args.onboarding_status, 'pending')
        logger.info("✓ Onboarding status correctly set to 'pending'")
        
        # Verify nullable fields are properly handled
        self.assertIsNone(db_call_args.native_language)
        self.assertIsNone(db_call_args.industry_id)
        self.assertIsNone(db_call_args.selected_role_id)
        self.assertIsNone(db_call_args.hierarchy_level)
        logger.info("✓ Supabase integration validated successfully")
        
        # Step 7: Validate response user data
        logger.info("Step 7: Validating response user data structure")
        user_data = response_data['user']
        
        self.assertEqual(user_data['id'], mock_db_user['id'])
        self.assertEqual(user_data['full_name'], self.test_user_data['full_name'])
        self.assertEqual(user_data['email'], self.test_user_data['email'])
        self.assertEqual(user_data['onboarding_status'], 'pending')
        self.assertTrue(user_data['is_active'])
        logger.info("✓ Response user data structure validated")
        
        # Step 8: Validate authentication tokens
        logger.info("Step 8: Validating authentication tokens")
        tokens = response_data['tokens']
        
        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertIn('token_type', tokens)
        self.assertIn('expires_in', tokens)
        
        # Validate token properties
        self.assertIsNotNone(tokens['access_token'])
        self.assertIsNotNone(tokens['refresh_token'])
        self.assertEqual(tokens['token_type'], 'Bearer')
        self.assertIsInstance(tokens['expires_in'], int)
        self.assertGreater(tokens['expires_in'], 0)
        logger.info("✓ Authentication tokens validated successfully")
        
        logger.info("=== SIGNUP FLOW TEST COMPLETED SUCCESSFULLY ===")
        logger.info("All validations passed:")
        logger.info("- Auth0 user creation ✓")
        logger.info("- Supabase user storage ✓")
        logger.info("- Onboarding status = 'pending' ✓")
        logger.info("- Authentication tokens ✓")
        logger.info("- Response structure ✓")
    
    def test_signup_validation_errors(self):
        """Test that signup properly validates required fields and constraints."""
        logger.info("=== TESTING SIGNUP VALIDATION ERRORS ===")
        
        # Test missing required fields
        test_cases = [
            ({}, "empty request"),
            ({'email': 'test@example.com'}, "missing full_name"),
            ({'full_name': 'Test User'}, "missing email"),
            ({'full_name': 'Test User', 'email': 'test@example.com'}, "missing password"),
            ({'full_name': 'Test User', 'email': 'test@example.com', 'password': 'pass123'}, "missing date_of_birth"),
        ]
        
        for invalid_data, test_name in test_cases:
            logger.info(f"Testing: {test_name}")
            response = self.client.post(
                self.signup_url,
                data=json.dumps(invalid_data),
                content_type='application/json'
            )
            
            # Should return validation error (400 Bad Request)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            logger.info(f"✓ {test_name} correctly rejected with 400")
    
    def test_duplicate_email_signup(self):
        """Test that duplicate email signup is properly rejected."""
        logger.info("=== TESTING DUPLICATE EMAIL SIGNUP ===")
        
        with patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email') as mock_get_by_email:
            # Mock that user already exists
            mock_get_by_email.return_value = {'id': 'existing-user-id', 'email': self.test_user_data['email']}
            
            response = self.client.post(
                self.signup_url,
                data=json.dumps(self.test_user_data),
                content_type='application/json'
            )
            
            # Should return conflict error
            self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
            logger.info("✓ Duplicate email correctly rejected with 409")