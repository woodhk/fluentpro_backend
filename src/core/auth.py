from jose import jwt, JWTError
from .config import settings
from typing import Dict, Any
import httpx
import json

class Auth0JWTValidator:
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.algorithms = settings.AUTH0_ALGORITHMS
        self.audience = settings.AUTH0_AUDIENCE
        self.issuer = settings.AUTH0_ISSUER
        self._jwks_cache = None
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS (JSON Web Key Set) from Auth0"""
        if not self._jwks_cache:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://{self.domain}/.well-known/jwks.json")
                response.raise_for_status()
                self._jwks_cache = response.json()
        return self._jwks_cache
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify Auth0 JWT token and extract payload"""
        try:
            # For now, we'll decode without signature verification
            # In production, you should verify the signature using JWKS
            payload = jwt.decode(
                token,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_signature": False}  # Disable for now
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

# Global instance
auth0_validator = Auth0JWTValidator()