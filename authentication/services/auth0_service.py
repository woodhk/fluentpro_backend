import requests
from django.conf import settings
from typing import Dict, Any, Optional
import json
import logging

from core.interfaces import AuthServiceInterface
from core.exceptions import AuthenticationError, ValidationError
from authentication.models.auth import TokenInfo

logger = logging.getLogger(__name__)


class Auth0Service(AuthServiceInterface):
    """
    Service class for interacting with Auth0 Management API
    """
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.audience = settings.AUTH0_AUDIENCE
        self._management_token = None
    
    def get_management_token(self) -> str:
        """
        Get Auth0 Management API access token
        """
        if self._management_token:
            return self._management_token
            
        url = f'https://{self.domain}/oauth/token'
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': f'https://{self.domain}/api/v2/'
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            self._management_token = response.json()['access_token']
            return self._management_token
        else:
            raise Exception(f'Failed to get management token: {response.text}')
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in Auth0 (implements AuthServiceInterface).
        """
        try:
            # Validate required fields
            if 'email' not in user_data or 'password' not in user_data:
                raise ValidationError("Email and password are required")
            
            url = f'https://{self.domain}/api/v2/users'
            headers = {
                'Authorization': f'Bearer {self.get_management_token()}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'email': user_data['email'],
                'password': user_data['password'],
                'connection': 'Username-Password-Authentication',
                'email_verified': False,
                'user_metadata': {
                    'full_name': user_data.get('full_name', '')
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_data = response.json()
                error_msg = error_data.get("message", response.text)
                logger.error(f"Auth0 user creation failed: {error_msg}")
                raise AuthenticationError(f'Failed to create user: {error_msg}')
                
        except requests.RequestException as e:
            logger.error(f"Auth0 user creation request failed: {str(e)}")
            raise AuthenticationError(f"User creation request failed: {str(e)}")
    
    def create_user_legacy(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Legacy method - create a new user in Auth0.
        Kept for backward compatibility.
        """
        return self.create_user({
            'email': email,
            'password': password,
            'full_name': full_name
        })
    
    def authenticate(self, email: str, password: str) -> TokenInfo:
        """
        Authenticate a user and get tokens (implements AuthServiceInterface).
        """
        try:
            url = f'https://{self.domain}/oauth/token'
            payload = {
                'grant_type': 'password',
                'username': email,
                'password': password,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'audience': self.audience,
                'scope': 'openid profile email'
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                token_data = response.json()
                return TokenInfo(
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token', ''),
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_in=token_data.get('expires_in', 3600),
                    scope=token_data.get('scope', 'openid profile email')
                )
            else:
                error_data = response.json()
                error_msg = error_data.get("error_description", response.text)
                logger.error(f"Auth0 authentication failed: {error_msg}")
                raise AuthenticationError(f'Authentication failed: {error_msg}')
                
        except requests.RequestException as e:
            logger.error(f"Auth0 request failed: {str(e)}")
            raise AuthenticationError(f"Authentication request failed: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Legacy method - authenticate a user and get tokens.
        Kept for backward compatibility.
        """
        token_info = self.authenticate(email, password)
        return token_info.to_dict()
    
    def refresh_token(self, refresh_token: str) -> TokenInfo:
        """
        Refresh access token using refresh token (implements AuthServiceInterface).
        """
        try:
            url = f'https://{self.domain}/oauth/token'
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                token_data = response.json()
                return TokenInfo(
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token', refresh_token),
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_in=token_data.get('expires_in', 3600),
                    scope=token_data.get('scope', 'openid profile email')
                )
            else:
                error_data = response.json()
                error_msg = error_data.get("error_description", response.text)
                logger.error(f"Auth0 token refresh failed: {error_msg}")
                raise AuthenticationError(f'Token refresh failed: {error_msg}')
                
        except requests.RequestException as e:
            logger.error(f"Auth0 refresh request failed: {str(e)}")
            raise AuthenticationError(f"Token refresh request failed: {str(e)}")
    
    def refresh_token_legacy(self, refresh_token: str) -> Dict[str, Any]:
        """
        Legacy method - refresh access token using refresh token.
        Kept for backward compatibility.
        """
        token_info = self.refresh_token(refresh_token)
        return token_info.to_dict()
    
    def logout_user(self, refresh_token: str) -> bool:
        """
        Logout user and revoke tokens (implements AuthServiceInterface).
        """
        try:
            url = f'https://{self.domain}/oauth/revoke'
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'token': refresh_token
            }
            
            response = requests.post(url, json=payload)
            success = response.status_code == 200
            
            if not success:
                logger.warning(f"Auth0 token revocation failed: {response.text}")
            
            return success
            
        except requests.RequestException as e:
            logger.error(f"Auth0 logout request failed: {str(e)}")
            return False
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Legacy method - revoke a refresh token (logout).
        Kept for backward compatibility.
        """
        return self.logout_user(refresh_token)
    
    def validate_token(self, access_token: str) -> Dict[str, Any]:
        """
        Validate access token and return user info (implements AuthServiceInterface).
        """
        try:
            url = f'https://{self.domain}/userinfo'
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f'Token validation failed: {response.text}'
                logger.error(f"Auth0 token validation failed: {error_msg}")
                raise AuthenticationError(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"Auth0 token validation request failed: {str(e)}")
            raise AuthenticationError(f"Token validation request failed: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Legacy method - get user information from Auth0.
        Kept for backward compatibility.
        """
        return self.validate_token(access_token)
    
    def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user metadata in Auth0
        """
        url = f'https://{self.domain}/api/v2/users/{user_id}'
        headers = {
            'Authorization': f'Bearer {self.get_management_token()}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'user_metadata': metadata
        }
        
        response = requests.patch(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Failed to update user metadata: {response.text}')
    
    def verify_email(self, user_id: str) -> bool:
        """
        Send email verification to user
        """
        url = f'https://{self.domain}/api/v2/jobs/verification-email'
        headers = {
            'Authorization': f'Bearer {self.get_management_token()}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'user_id': user_id,
            'client_id': self.client_id
        }
        
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201]