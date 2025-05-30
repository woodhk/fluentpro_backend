import json
import jwt
import requests
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework import authentication, exceptions


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication backend for Auth0 JWT tokens
    """
    
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        
        if not auth_header or auth_header[0].lower() != b'bearer':
            return None
            
        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')
            
        try:
            token = auth_header[1].decode('utf-8')
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Invalid token. Token string should not contain invalid characters.')
            
        try:
            payload = self.verify_token(token)
        except jwt.PyJWTError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
            
        user = self.get_or_create_user(payload)
        return (user, token)
    
    def verify_token(self, token):
        """
        Verify the Auth0 JWT token
        """
        # Get the JWT signing keys from Auth0
        jwks_url = f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json'
        jwks = requests.get(jwks_url).json()
        
        # Get the key id from the token header
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the key
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
                break
                
        if rsa_key:
            try:
                # Verify the token
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=['RS256'],
                    audience=settings.AUTH0_AUDIENCE,
                    issuer=f'https://{settings.AUTH0_DOMAIN}/'
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise exceptions.AuthenticationFailed('Token has expired')
            except jwt.InvalidAudienceError:
                raise exceptions.AuthenticationFailed('Invalid audience')
            except jwt.InvalidIssuerError:
                raise exceptions.AuthenticationFailed('Invalid issuer')
            except Exception as e:
                raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        else:
            raise exceptions.AuthenticationFailed('Unable to find appropriate key')
    
    def get_or_create_user(self, payload):
        """
        Get or create a user based on the Auth0 payload
        We'll return a simple user object that can be used in views
        """
        from authentication.models import SimpleUser
        
        # Extract user information from the payload
        auth0_user_id = payload.get('sub')
        email = payload.get('email')
        
        # In a production environment, you might want to create actual Django users
        # For now, we'll return a simple user object
        user = SimpleUser(
            auth0_id=auth0_user_id,
            email=email,
            is_authenticated=True
        )
        
        return user