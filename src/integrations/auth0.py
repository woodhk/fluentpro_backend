import httpx
from typing import Dict, Any, Optional
from ..core.config import settings

class Auth0ManagementClient:
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.audience = f"https://{self.domain}/api/v2/"
        self._management_token = None
    
    async def get_management_token(self) -> str:
        """Get Auth0 Management API token"""
        if self._management_token:
            return self._management_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.domain}/oauth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": self.audience,
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            token_data = response.json()
            self._management_token = token_data["access_token"]
            return self._management_token
    
    async def get_user_profile(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Auth0 Management API"""
        try:
            token = await self.get_management_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.domain}/api/v2/users/{auth0_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting Auth0 user profile: {e}")
            return None
    
    async def update_user_metadata(self, auth0_id: str, user_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user metadata in Auth0"""
        try:
            token = await self.get_management_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://{self.domain}/api/v2/users/{auth0_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"user_metadata": user_metadata}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error updating Auth0 user metadata: {e}")
            return None

# Global instance
auth0_client = Auth0ManagementClient()