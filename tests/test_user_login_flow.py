"""
Test suite for comprehensive user login flow validation.

This test validates the complete login process including:
- Auth0 credential verification
- Supabase user data retrieval
- Proper onboarding_status handling for frontend routing
- Authentication token generation and validation

Expected behavior based on legacy implementation (commit fede7002f840...):
- User credentials should be verified via Auth0
- User data should be retrieved from Supabase with current onboarding_status
- Frontend routing logic based on onboarding_status:
  - 'completed' → redirect to homepage
  - Other statuses ('pending', 'welcome', 'basic_info', 'personalisation', 'course_assignment') → redirect to onboarding flow
- Response should include valid authentication tokens and user data
"""

import pytest
import json
import logging
from datetime import date, datetime
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

# Configure detailed logging for test debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserLoginFlowTest(TestCase):
    """Comprehensive test for user login flow and onboarding status handling."""
    
    def setUp(self):
        """Set up test environment with API client and test data."""
        self.client = APIClient()
        self.login_url = '/api/v1/auth/sessions/login/'
        
        # Test user credentials
        self.test_credentials = {
            'email': 'john.smith.test@example.com',
            'password': 'SecurePassword123!'
        }
        
        # Mock user data that would exist in Supabase
        self.mock_user_base = {
            'id': 'user-uuid-123',
            'full_name': 'John Alexander Smith',
            'email': 'john.smith.test@example.com',
            'date_of_birth': '1990-05-15',
            'auth0_id': 'auth0|abc123def456',
            'is_active': True,
            'native_language': None,
            'industry_id': None,
            'selected_role_id': None,
            'hierarchy_level': None,
            'created_at': '2025-06-09T10:00:00.000Z',
            'updated_at': '2025-06-09T10:00:00.000Z'
        }
        
        logger.info("=== LOGIN TEST SETUP COMPLETE ===")
        logger.info(f"Test user email: {self.test_credentials['email']}")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_login_with_completed_onboarding(self, mock_get_user, mock_auth0_authenticate):
        """
        Test login flow for user with completed onboarding.
        
        Expected behavior:
        - User should be authenticated via Auth0
        - User data retrieved from Supabase
        - onboarding_status should be 'completed'
        - Frontend should redirect to homepage
        """
        logger.info("=== TESTING LOGIN WITH COMPLETED ONBOARDING ===")
        
        # Step 1: Setup Auth0 authentication mock
        logger.info("Step 1: Setting up Auth0 authentication mock")
        mock_auth0_tokens = {
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            'refresh_token': 'refresh_token_abc123',
            'token_type': 'Bearer',
            'expires_in': 86400
        }
        mock_auth0_authenticate.return_value = mock_auth0_tokens
        logger.info("✓ Auth0 authentication mock configured")
        
        # Step 2: Setup Supabase user data mock (completed onboarding)
        logger.info("Step 2: Setting up Supabase user data mock")
        mock_user = {**self.mock_user_base, 'onboarding_status': 'completed'}
        mock_get_user.return_value = mock_user
        logger.info(f"Mock user onboarding_status: {mock_user['onboarding_status']}")
        
        # Step 3: Execute login request
        logger.info("Step 3: Making login API request")
        logger.info(f"Request URL: {self.login_url}")
        logger.info(f"Request credentials: {json.dumps({'email': self.test_credentials['email'], 'password': '***'}, indent=2)}")
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response data: {json.dumps(response.json() if response.content else {}, indent=2)}")
        
        # Step 4: Validate response structure and status
        logger.info("Step 4: Validating response structure")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('user', response_data)
        self.assertIn('tokens', response_data)
        
        # Step 5: Validate Auth0 authentication was called
        logger.info("Step 5: Validating Auth0 authentication")
        mock_auth0_authenticate.assert_called_once_with(
            email=self.test_credentials['email'],
            password=self.test_credentials['password']
        )
        logger.info("✓ Auth0 authentication validated")
        
        # Step 6: Validate user data retrieval from Supabase
        logger.info("Step 6: Validating Supabase user data retrieval")
        mock_get_user.assert_called_once_with(self.test_credentials['email'])
        logger.info("✓ Supabase user retrieval validated")
        
        # Step 7: Validate response user data
        logger.info("Step 7: Validating response user data")
        user_data = response_data['user']
        
        self.assertEqual(user_data['id'], mock_user['id'])
        self.assertEqual(user_data['full_name'], mock_user['full_name'])
        self.assertEqual(user_data['email'], mock_user['email'])
        self.assertEqual(user_data['onboarding_status'], 'completed')
        self.assertTrue(user_data['is_active'])
        logger.info("✓ User data structure validated")
        logger.info(f"✓ Onboarding status confirmed as: {user_data['onboarding_status']}")
        
        # Step 8: Validate authentication tokens
        logger.info("Step 8: Validating authentication tokens")
        tokens = response_data['tokens']
        
        self.assertEqual(tokens['access_token'], mock_auth0_tokens['access_token'])
        self.assertEqual(tokens['refresh_token'], mock_auth0_tokens['refresh_token'])
        self.assertEqual(tokens['token_type'], 'Bearer')
        self.assertEqual(tokens['expires_in'], 86400)
        logger.info("✓ Authentication tokens validated")
        
        logger.info("=== LOGIN WITH COMPLETED ONBOARDING TEST PASSED ===")
        logger.info("Frontend should redirect to HOMEPAGE")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_login_with_pending_onboarding(self, mock_get_user, mock_auth0_authenticate):
        """
        Test login flow for user with pending onboarding.
        
        Expected behavior:
        - User should be authenticated via Auth0
        - User data retrieved from Supabase
        - onboarding_status should be 'pending'
        - Frontend should redirect to onboarding flow
        """
        logger.info("=== TESTING LOGIN WITH PENDING ONBOARDING ===")
        
        # Setup Auth0 authentication mock
        mock_auth0_tokens = {
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            'refresh_token': 'refresh_token_def456',
            'token_type': 'Bearer',
            'expires_in': 86400
        }
        mock_auth0_authenticate.return_value = mock_auth0_tokens
        
        # Setup Supabase user data mock (pending onboarding)
        mock_user = {**self.mock_user_base, 'onboarding_status': 'pending'}
        mock_get_user.return_value = mock_user
        logger.info(f"Mock user onboarding_status: {mock_user['onboarding_status']}")
        
        # Execute login request
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Critical validation: onboarding_status should be 'pending'
        user_data = response_data['user']
        self.assertEqual(user_data['onboarding_status'], 'pending')
        logger.info(f"✓ Onboarding status confirmed as: {user_data['onboarding_status']}")
        
        logger.info("=== LOGIN WITH PENDING ONBOARDING TEST PASSED ===")
        logger.info("Frontend should redirect to ONBOARDING FLOW")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_login_with_personalisation_onboarding(self, mock_get_user, mock_auth0_authenticate):
        """
        Test login flow for user in personalisation step of onboarding.
        
        Expected behavior:
        - User should be authenticated via Auth0
        - User data retrieved from Supabase
        - onboarding_status should be 'personalisation'
        - Frontend should redirect to personalisation step in onboarding
        """
        logger.info("=== TESTING LOGIN WITH PERSONALISATION ONBOARDING ===")
        
        # Setup mocks
        mock_auth0_tokens = {
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            'refresh_token': 'refresh_token_ghi789',
            'token_type': 'Bearer',
            'expires_in': 86400
        }
        mock_auth0_authenticate.return_value = mock_auth0_tokens
        
        # User in personalisation step with some fields filled
        mock_user = {
            **self.mock_user_base,
            'onboarding_status': 'personalisation',
            'native_language': 'english',  # User has completed native language step
            'industry_id': 'industry-uuid-123'  # User has selected industry
        }
        mock_get_user.return_value = mock_user
        logger.info(f"Mock user onboarding_status: {mock_user['onboarding_status']}")
        logger.info(f"Mock user native_language: {mock_user['native_language']}")
        
        # Execute login request
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Critical validation: onboarding_status should be 'personalisation'
        user_data = response_data['user']
        self.assertEqual(user_data['onboarding_status'], 'personalisation')
        self.assertEqual(user_data['native_language'], 'english')
        logger.info(f"✓ Onboarding status confirmed as: {user_data['onboarding_status']}")
        
        logger.info("=== LOGIN WITH PERSONALISATION ONBOARDING TEST PASSED ===")
        logger.info("Frontend should redirect to PERSONALISATION STEP in onboarding")
    
    def test_all_valid_onboarding_statuses(self):
        """
        Test that all valid onboarding statuses are properly handled.
        
        Valid statuses from Supabase schema:
        - 'pending', 'welcome', 'basic_info', 'personalisation', 'course_assignment', 'completed'
        """
        logger.info("=== TESTING ALL VALID ONBOARDING STATUSES ===")
        
        valid_statuses = ['pending', 'welcome', 'basic_info', 'personalisation', 'course_assignment', 'completed']
        
        for status_value in valid_statuses:
            with self.subTest(onboarding_status=status_value):
                logger.info(f"Testing onboarding_status: {status_value}")
                
                with patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate') as mock_auth0, \
                     patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email') as mock_get_user:
                    
                    # Setup mocks
                    mock_auth0.return_value = {
                        'access_token': 'token',
                        'refresh_token': 'refresh',
                        'token_type': 'Bearer',
                        'expires_in': 86400
                    }
                    
                    mock_user = {**self.mock_user_base, 'onboarding_status': status_value}
                    mock_get_user.return_value = mock_user
                    
                    # Execute request
                    response = self.client.post(
                        self.login_url,
                        data=json.dumps(self.test_credentials),
                        content_type='application/json'
                    )
                    
                    # Validate response
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(response_data['user']['onboarding_status'], status_value)
                    
                    # Log expected frontend behavior
                    if status_value == 'completed':
                        logger.info(f"✓ {status_value} → Frontend should redirect to HOMEPAGE")
                    else:
                        logger.info(f"✓ {status_value} → Frontend should redirect to ONBOARDING FLOW")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    def test_login_invalid_credentials(self, mock_auth0_authenticate):
        """Test that invalid credentials are properly rejected."""
        logger.info("=== TESTING LOGIN WITH INVALID CREDENTIALS ===")
        
        # Mock Auth0 to raise authentication error
        from core.exceptions import AuthenticationError
        mock_auth0_authenticate.side_effect = AuthenticationError("Invalid credentials")
        
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': 'invalid@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        # Should return authentication error
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        logger.info("✓ Invalid credentials correctly rejected with 401")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_login_inactive_user(self, mock_get_user, mock_auth0_authenticate):
        """Test that inactive users cannot login."""
        logger.info("=== TESTING LOGIN WITH INACTIVE USER ===")
        
        # Setup Auth0 authentication success
        mock_auth0_authenticate.return_value = {
            'access_token': 'token',
            'refresh_token': 'refresh',
            'token_type': 'Bearer',
            'expires_in': 86400
        }
        
        # Setup inactive user in Supabase
        mock_user = {**self.mock_user_base, 'is_active': False}
        mock_get_user.return_value = mock_user
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Should return forbidden error
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        logger.info("✓ Inactive user correctly rejected with 403")
    
    def test_login_validation_errors(self):
        """Test that login properly validates required fields."""
        logger.info("=== TESTING LOGIN VALIDATION ERRORS ===")
        
        test_cases = [
            ({}, "empty request"),
            ({'email': 'test@example.com'}, "missing password"),
            ({'password': 'password123'}, "missing email"),
            ({'email': 'invalid-email', 'password': 'pass123'}, "invalid email format"),
        ]
        
        for invalid_data, test_name in test_cases:
            logger.info(f"Testing: {test_name}")
            response = self.client.post(
                self.login_url,
                data=json.dumps(invalid_data),
                content_type='application/json'
            )
            
            # Should return validation error (400 Bad Request)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            logger.info(f"✓ {test_name} correctly rejected with 400")
    
    @patch('infrastructure.external_services.auth0.auth0_service_impl.Auth0ServiceImpl.authenticate')
    @patch('infrastructure.persistence.supabase.implementations.user_repository_impl.UserRepositoryImpl.get_by_email')
    def test_login_user_not_found_in_database(self, mock_get_user, mock_auth0_authenticate):
        """Test login when user exists in Auth0 but not in Supabase."""
        logger.info("=== TESTING LOGIN USER NOT FOUND IN DATABASE ===")
        
        # Setup Auth0 authentication success
        mock_auth0_authenticate.return_value = {
            'access_token': 'token',
            'refresh_token': 'refresh',
            'token_type': 'Bearer',
            'expires_in': 86400
        }
        
        # User not found in Supabase
        mock_get_user.return_value = None
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Should return not found error
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        logger.info("✓ User not found in database correctly rejected with 404")