from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from authentication.serializers import (
    SignUpSerializer, LoginSerializer, AuthResponseSerializer,
    RefreshTokenSerializer, LogoutSerializer, Auth0CallbackSerializer,
    UserSerializer
)
from authentication.services.auth0_service import Auth0Service
from authentication.services.supabase_service import SupabaseService
from authentication.services.azure_search_service import AzureSearchService
from authentication.services.azure_openai_service import AzureOpenAIService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(APIView):
    """
    User sign up endpoint
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            auth0_service = Auth0Service()
            supabase_service = SupabaseService()
            
            # Extract validated data
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            full_name = serializer.validated_data['full_name']
            date_of_birth = serializer.validated_data['date_of_birth']
            
            # Check if user already exists in Supabase
            existing_user = supabase_service.get_user_by_email(email)
            if existing_user:
                return Response({
                    'error': 'User already exists',
                    'message': 'A user with this email already exists'
                }, status=status.HTTP_409_CONFLICT)
            
            # Create user in Auth0
            auth0_user = auth0_service.create_user(email, password, full_name)
            
            # Create user in Supabase
            user_data = {
                'full_name': full_name,
                'email': email,
                'date_of_birth': date_of_birth.isoformat(),
                'auth0_id': auth0_user['user_id'],
                'is_active': True
            }
            
            supabase_user = supabase_service.create_user(user_data)
            
            # Authenticate the user to get tokens
            auth_response = auth0_service.authenticate_user(email, password)
            
            # Prepare response
            response_data = {
                'access_token': auth_response['access_token'],
                'refresh_token': auth_response.get('refresh_token'),
                'token_type': auth_response.get('token_type', 'Bearer'),
                'expires_in': auth_response.get('expires_in', 3600),
                'user': {
                    'id': supabase_user['id'],
                    'full_name': supabase_user['full_name'],
                    'email': supabase_user['email'],
                    'date_of_birth': supabase_user['date_of_birth']
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Sign up error: {str(e)}")
            return Response({
                'error': 'Sign up failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    User login endpoint
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            auth0_service = Auth0Service()
            supabase_service = SupabaseService()
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate with Auth0
            auth_response = auth0_service.authenticate_user(email, password)
            
            # Get user from Supabase
            user = supabase_service.get_user_by_email(email)
            
            if not user:
                return Response({
                    'error': 'User not found',
                    'message': 'User does not exist in our system'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Prepare response
            response_data = {
                'access_token': auth_response['access_token'],
                'refresh_token': auth_response.get('refresh_token'),
                'token_type': auth_response.get('token_type', 'Bearer'),
                'expires_in': auth_response.get('expires_in', 3600),
                'user': {
                    'id': user['id'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'date_of_birth': user['date_of_birth']
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            
            # Check if it's an authentication error
            if 'invalid_grant' in str(e).lower() or 'invalid credentials' in str(e).lower():
                return Response({
                    'error': 'Invalid credentials',
                    'message': 'Email or password is incorrect'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            return Response({
                'error': 'Login failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(APIView):
    """
    Refresh access token endpoint
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            auth0_service = Auth0Service()
            refresh_token = serializer.validated_data['refresh_token']
            
            # Refresh token with Auth0
            auth_response = auth0_service.refresh_token(refresh_token)
            
            response_data = {
                'access_token': auth_response['access_token'],
                'refresh_token': auth_response.get('refresh_token', refresh_token),
                'token_type': auth_response.get('token_type', 'Bearer'),
                'expires_in': auth_response.get('expires_in', 3600)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response({
                'error': 'Token refresh failed',
                'message': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """
    User logout endpoint
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            auth0_service = Auth0Service()
            refresh_token = serializer.validated_data['refresh_token']
            
            # Revoke refresh token
            auth0_service.revoke_refresh_token(refresh_token)
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': 'Logout failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class Auth0CallbackView(APIView):
    """
    Auth0 callback endpoint for OAuth flows
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = Auth0CallbackSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # This endpoint can be extended to handle OAuth callback flows
            # For now, it's a placeholder
            return Response({
                'message': 'Auth0 callback received'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Auth0 callback error: {str(e)}")
            return Response({
                'error': 'Callback processing failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(APIView):
    """
    Get current user profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            supabase_service = SupabaseService()
            
            # Get user from Supabase using email from JWT
            user = supabase_service.get_user_by_email(request.user.email)
            
            if not user:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user_data = {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'date_of_birth': user['date_of_birth'],
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at')
            }
            
            return Response(user_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"User profile error: {str(e)}")
            return Response({
                'error': 'Failed to get user profile',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobInputView(APIView):
    """
    Phase 2 Step 1: User inputs job title and description for role matching
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Extract job data from request
            job_title = request.data.get('job_title', '').strip()
            job_description = request.data.get('job_description', '').strip()
            
            if not job_title:
                return Response({
                    'error': 'Validation failed',
                    'message': 'Job title is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not job_description:
                return Response({
                    'error': 'Validation failed',
                    'message': 'Job description is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize services
            supabase_service = SupabaseService()
            azure_search_service = AzureSearchService()
            azure_openai_service = AzureOpenAIService()
            
            # Get user profile to get their industry
            user_profile = supabase_service.get_user_full_profile(request.user.sub)
            
            if not user_profile:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if not user_profile.get('industry_name'):
                return Response({
                    'error': 'User industry not set',
                    'message': 'Please complete industry selection first'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create comprehensive query text for embedding
            query_text = f"Job Title: {job_title}\nIndustry: {user_profile['industry_name']}\nDescription: {job_description}"
            
            # Generate embedding for the user's job input
            query_embedding = azure_openai_service.get_embedding(query_text)
            
            # Search for similar roles with industry filter
            industry_filter = f"industry_name eq '{user_profile['industry_name']}'"
            
            # Use hybrid search combining text and vector similarity
            search_result = azure_search_service.hybrid_search_roles(
                text_query=f"{job_title} {job_description}",
                query_embedding=query_embedding,
                top_k=5,
                filters=industry_filter
            )
            
            if not search_result['success']:
                return Response({
                    'error': 'Role search failed',
                    'message': search_result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Format results
            matched_roles = []
            for role in search_result['results']:
                matched_roles.append({
                    'id': role['id'],
                    'title': role['title'],
                    'description': role['description'],
                    'industry_name': role['industry_name'],
                    'hierarchy_level': role['hierarchy_level'],
                    'search_keywords': role.get('search_keywords', ''),
                    'relevance_score': role['score']
                })
            
            return Response({
                'success': True,
                'user_job_input': {
                    'job_title': job_title,
                    'job_description': job_description,
                    'user_industry': user_profile['industry_name']
                },
                'matched_roles': matched_roles,
                'total_matches': len(matched_roles)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Job input processing error: {str(e)}")
            return Response({
                'error': 'Job input processing failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RoleSelectionView(APIView):
    """
    Phase 2 Step 1: User selects a role and updates their selected_role_id
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Extract role ID from request
            role_id = request.data.get('role_id', '').strip()
            
            if not role_id:
                return Response({
                    'error': 'Validation failed',
                    'message': 'Role ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize Supabase service
            supabase_service = SupabaseService()
            
            # Update user's selected role
            update_result = supabase_service.update_user_selected_role(
                auth0_id=request.user.sub,
                role_id=role_id
            )
            
            if not update_result['success']:
                return Response({
                    'error': 'Role selection failed',
                    'message': update_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get updated user profile
            user_profile = supabase_service.get_user_full_profile(request.user.sub)
            
            return Response({
                'success': True,
                'message': 'Role selected successfully',
                'user_id': update_result['user_id'],
                'selected_role': {
                    'id': update_result['selected_role_id'],
                    'title': update_result['role_title']
                },
                'user_profile': {
                    'native_language': user_profile['native_language'],
                    'industry_name': user_profile['industry_name'],
                    'role_title': user_profile['role_title'],
                    'onboarding_status': user_profile['onboarding_status']
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Role selection error: {str(e)}")
            return Response({
                'error': 'Role selection failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)