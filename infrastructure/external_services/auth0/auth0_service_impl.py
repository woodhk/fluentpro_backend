"""
Auth0 Service Implementation

Concrete implementation of authentication service using Auth0.
"""

from domains.authentication.services.interfaces import IAuthenticationService
from infrastructure.external_services.auth0.client import IAuth0Client
from application.decorators.retry import retry
from application.decorators.circuit_breaker import circuit_breaker
from application.exceptions.infrastructure_exceptions import ExternalServiceException
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Auth0ServiceImpl(IAuthenticationService):
    """
    Auth0 implementation of authentication service.
    
    Provides user management and authentication using Auth0 as the provider.
    """
    
    def __init__(self, client: IAuth0Client):
        self.client = client
    
    @retry(max_attempts=3, backoff_seconds=1)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        """
        Create a user in Auth0.
        
        Args:
            email: User's email address
            password: User's password
            metadata: Additional user metadata
            
        Returns:
            Auth0 user ID
            
        Raises:
            ExternalServiceException: If user creation fails
        """
        try:
            logger.info(f"Creating Auth0 user for email: {email}")
            
            response = await self.client.create_user(
                email=email,
                password=password,
                connection="Username-Password-Authentication",
                user_metadata=metadata
            )
            
            user_id = response.get('user_id')
            if not user_id:
                raise ExternalServiceException("Auth0 did not return user_id")
            
            logger.info(f"Successfully created Auth0 user: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to create Auth0 user for {email}: {e}")
            if isinstance(e, ExternalServiceException):
                raise
            
            raise ExternalServiceException(f"Authentication service error: {str(e)}")
    
    @retry(max_attempts=2, backoff_seconds=0.5)
    @circuit_breaker(failure_threshold=10, recovery_timeout=30)
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token using Auth0.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token claims if valid, None if invalid
            
        Note:
            This method returns None for invalid tokens rather than raising
            exceptions, as token verification is often used in authentication
            middleware where invalid tokens are expected.
        """
        try:
            logger.debug("Verifying Auth0 token")
            
            claims = await self.client.verify_token(token)
            
            if claims:
                logger.debug(f"Token verified successfully for user: {claims.get('sub')}")
            else:
                logger.debug("Token verification failed - invalid token")
            
            return claims
            
        except Exception as e:
            logger.warning(f"Token verification error: {e}")
            # For token verification, we return None on any error
            # rather than raising exceptions
            return None
    
    @retry(max_attempts=3, backoff_seconds=1)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token in Auth0.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revocation successful
            
        Raises:
            ExternalServiceException: If token revocation fails
        """
        try:
            logger.info("Revoking Auth0 token")
            
            success = await self.client.revoke_refresh_token(token)
            
            if success:
                logger.info("Token revoked successfully")
            else:
                logger.warning("Token revocation returned false")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            raise ExternalServiceException(f"Token revocation failed: {str(e)}")