import requests
from django.conf import settings
from typing import Dict, Any, Optional
import json


class Auth0Service:
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
    
    def create_user(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """
        Create a new user in Auth0
        """
        url = f'https://{self.domain}/api/v2/users'
        headers = {
            'Authorization': f'Bearer {self.get_management_token()}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'email': email,
            'password': password,
            'connection': 'Username-Password-Authentication',
            'email_verified': False,
            'user_metadata': {
                'full_name': full_name
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_data = response.json()
            raise Exception(f'Failed to create user: {error_data.get("message", response.text)}')
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and get tokens
        """
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
            return response.json()
        else:
            error_data = response.json()
            raise Exception(f'Authentication failed: {error_data.get("error_description", response.text)}')
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        """
        url = f'https://{self.domain}/oauth/token'
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            raise Exception(f'Token refresh failed: {error_data.get("error_description", response.text)}')
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token (logout)
        """
        url = f'https://{self.domain}/oauth/revoke'
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'token': refresh_token
        }
        
        response = requests.post(url, json=payload)
        return response.status_code == 200
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Auth0
        """
        url = f'https://{self.domain}/userinfo'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Failed to get user info: {response.text}')
    
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