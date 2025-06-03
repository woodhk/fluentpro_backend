"""
Role management views for FluentPro v1.
Handles job input, role matching, and role creation workflows.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError, BusinessLogicError
from authentication.business.user_manager import UserManager
from authentication.business.role_manager import RoleManager

logger = logging.getLogger(__name__)


class JobInputView(AuthenticatedView, VersionedView):
    """
    Job input and role matching endpoint.
    Phase 2 Step 1: User inputs job description and gets role matches.
    """
    
    def post(self, request):
        """Process job input and return role matches."""
        try:
            # Validate input
            job_title = request.data.get('job_title', '').strip()
            job_description = request.data.get('job_description', '').strip()
            
            if not job_title:
                raise ValidationError("Job title is required")
            
            if not job_description:
                raise ValidationError("Job description is required")
            
            # Get current user and validate industry
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(self.get_auth0_user_id())
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not user_profile.industry_name:
                raise ValidationError("Please complete industry selection first")
            
            # Use role manager for role matching
            role_manager = RoleManager()
            
            # Create job input for embedding and search
            job_input = {
                'title': job_title,
                'description': job_description,
                'industry': user_profile.industry_name
            }
            
            # Find matching roles
            matched_roles = role_manager.find_matching_roles(
                job_input=job_input,
                industry_filter=user_profile.industry_name,
                limit=5
            )
            
            # Format response
            formatted_roles = []
            for role_match in matched_roles:
                formatted_roles.append({
                    'id': role_match.role.id,
                    'title': role_match.role.title,
                    'description': role_match.role.description,
                    'industry_name': role_match.role.industry_name,
                    'hierarchy_level': role_match.role.hierarchy_level.value,
                    'search_keywords': role_match.role.search_keywords,
                    'relevance_score': role_match.similarity_score
                })
            
            return APIResponse.success(
                data={
                    'user_job_input': {
                        'job_title': job_title,
                        'job_description': job_description,
                        'user_industry': user_profile.industry_name
                    },
                    'matched_roles': formatted_roles,
                    'total_matches': len(formatted_roles)
                }
            )
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Job input processing error: {str(e)}")
            return APIResponse.error(
                message="Job input processing failed",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoleSelectionView(AuthenticatedView, VersionedView):
    """
    Role selection endpoint.
    Phase 2 Step 1: User selects a role from matches.
    """
    
    def post(self, request):
        """Handle role selection."""
        try:
            # Validate input
            role_id = request.data.get('role_id', '').strip()
            
            if not role_id:
                raise ValidationError("Role ID is required")
            
            # Use user manager to update selected role
            user_manager = UserManager()
            auth0_id = self.get_auth0_user_id()
            
            # Update user's selected role
            update_result = user_manager.update_selected_role(auth0_id, role_id)
            
            # Track role source as selected
            role_manager = RoleManager()
            role_manager.track_role_selection(
                auth0_id=auth0_id,
                role_id=role_id,
                source='selected'
            )
            
            # Get updated user profile
            user_profile = user_manager.get_user_profile(auth0_id)
            
            return APIResponse.success(
                data={
                    'message': 'Role selected successfully',
                    'selected_role': {
                        'id': role_id,
                        'title': update_result.get('role_title')
                    },
                    'role_source': 'selected',
                    'user_profile': {
                        'native_language': user_profile.native_language.value if user_profile.native_language else None,
                        'industry_name': user_profile.industry_name,
                        'role_title': user_profile.role_title,
                        'onboarding_status': user_profile.onboarding_status.value
                    }
                }
            )
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"Role selection error: {str(e)}")
            return APIResponse.error(
                message="Role selection failed",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NewRoleCreationView(AuthenticatedView, VersionedView):
    """
    New role creation endpoint.
    Phase 2 Step 2: Create new role when user rejects all matches.
    """
    
    def post(self, request):
        """Handle new role creation."""
        try:
            # Validate input
            job_title = request.data.get('job_title', '').strip()
            job_description = request.data.get('job_description', '').strip()
            hierarchy_level = request.data.get('hierarchy_level', 'associate').strip()
            
            if not job_title:
                raise ValidationError("Job title is required")
            
            if not job_description:
                raise ValidationError("Job description is required")
            
            # Validate hierarchy level
            valid_levels = ['associate', 'supervisor', 'manager', 'director']
            if hierarchy_level not in valid_levels:
                hierarchy_level = 'associate'  # Default fallback
            
            # Get current user
            user_manager = UserManager()
            user_profile = user_manager.get_user_profile(self.get_auth0_user_id())
            
            if not user_profile:
                return APIResponse.error(
                    message="User not found",
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not user_profile.industry_id:
                raise ValidationError("Please complete industry selection first")
            
            # Use role manager for role creation
            role_manager = RoleManager()
            
            # Create new role with LLM enhancement
            new_role = role_manager.create_new_role(
                title=job_title,
                description=job_description,
                industry_id=user_profile.industry_id,
                hierarchy_level=hierarchy_level,
                created_by_user_id=user_profile.user.id
            )
            
            # Update user's selected role to the new role
            auth0_id = self.get_auth0_user_id()
            user_manager.update_selected_role(auth0_id, new_role.id)
            
            # Track role source as created
            role_manager.track_role_selection(
                auth0_id=auth0_id,
                role_id=new_role.id,
                source='created',
                original_description=job_description
            )
            
            # Get updated user profile
            updated_profile = user_manager.get_user_profile(auth0_id)
            
            return APIResponse.success(
                data={
                    'message': 'New role created and selected successfully',
                    'new_role': {
                        'id': new_role.id,
                        'title': new_role.title,
                        'description': new_role.description,
                        'original_description': job_description,
                        'hierarchy_level': new_role.hierarchy_level.value,
                        'generated_keywords': new_role.search_keywords,
                        'industry_name': user_profile.industry_name
                    },
                    'role_source': 'created',
                    'user_profile': {
                        'native_language': updated_profile.native_language.value if updated_profile.native_language else None,
                        'industry_name': updated_profile.industry_name,
                        'role_title': updated_profile.role_title,
                        'onboarding_status': updated_profile.onboarding_status.value
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"New role creation error: {str(e)}")
            return APIResponse.error(
                message="New role creation failed",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoleSearchView(CachedView, VersionedView):
    """
    Role search endpoint with caching.
    Provides search functionality for roles.
    """
    cache_timeout = 300  # 5 minutes cache
    
    def get(self, request):
        """Search for roles."""
        try:
            query = request.GET.get('q', '').strip()
            industry_filter = request.GET.get('industry')
            limit = min(int(request.GET.get('limit', 10)), 50)
            
            if not query:
                raise ValidationError("Search query is required")
            
            # Check cache
            cache_key = self.get_cache_key("search", query, industry_filter, limit)
            cached_results = self.get_cached_response(cache_key)
            
            if cached_results:
                return APIResponse.success(data=cached_results)
            
            # Search using role manager
            role_manager = RoleManager()
            search_results = role_manager.search_roles(
                query=query,
                industry_filter=industry_filter,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for role_match in search_results:
                formatted_results.append({
                    'id': role_match.role.id,
                    'title': role_match.role.title,
                    'description': role_match.role.description,
                    'industry_name': role_match.role.industry_name,
                    'hierarchy_level': role_match.role.hierarchy_level.value,
                    'relevance_score': role_match.similarity_score
                })
            
            results_data = {
                'query': query,
                'results': formatted_results,
                'total_results': len(formatted_results)
            }
            
            # Cache results
            self.set_cached_response(cache_key, results_data)
            
            return APIResponse.success(data=results_data)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Role search error: {str(e)}")
            return APIResponse.error(
                message="Role search failed",
                details=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )