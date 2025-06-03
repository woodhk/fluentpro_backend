import json
import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
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
        except (JWTError, ExpiredSignatureError, JWTClaimsError) as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
            
        user = self.get_or_create_user(payload)
        return (user, token)
    
    def verify_token(self, token):
        """
        Verify the Auth0 JWT token
        """
        try:
            # Get the JWT signing keys from Auth0
            jwks_url = f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json'
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Get the key id from the token header
            unverified_header = jwt.get_unverified_header(token)
            
            # Find the key
            rsa_key = None
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    rsa_key = key
                    break
                    
            if not rsa_key:
                raise exceptions.AuthenticationFailed('Unable to find appropriate key')
            
            # Verify the token using python-jose
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=settings.AUTH0_AUDIENCE,
                issuer=f'https://{settings.AUTH0_DOMAIN}/'
            )
            return payload
            
        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except JWTClaimsError as e:
            if 'audience' in str(e).lower():
                raise exceptions.AuthenticationFailed('Invalid audience')
            elif 'issuer' in str(e).lower():
                raise exceptions.AuthenticationFailed('Invalid issuer')
            else:
                raise exceptions.AuthenticationFailed(f'Token claims error: {str(e)}')
        except requests.RequestException as e:
            raise exceptions.AuthenticationFailed(f'Failed to fetch JWKS: {str(e)}')
        except JWTError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token verification failed: {str(e)}')
    
    def get_or_create_user(self, payload):
        """
        Get or create a user based on the Auth0 payload
        Returns a simple user object that can be used in views
        """
        # Extract user information from the payload
        auth0_user_id = payload.get('sub')
        email = payload.get('email')
        
        # Create a simple user object for authentication
        user = SimpleUser(
            auth0_id=auth0_user_id,
            email=email,
            is_authenticated=True
        )
        
        return user


class SimpleUser:
    """
    Simple user object for JWT authentication that mimics Django User interface
    """
    def __init__(self, auth0_id=None, email=None, is_authenticated=False):
        self.auth0_id = auth0_id
        self.email = email
        self.is_authenticated = is_authenticated
        self.is_anonymous = False
        self.is_active = True
        # Store auth0_id as 'sub' for compatibility with existing code
        self.sub = auth0_id
    
    @property
    def is_staff(self):
        return False
    
    @property
    def is_superuser(self):
        return False
    
    def get_username(self):
        return self.email or self.auth0_id
    
    def __str__(self):
        return self.get_username() or 'Anonymous'