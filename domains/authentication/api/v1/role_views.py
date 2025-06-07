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
from authentication.models.role import JobDescription

logger = logging.getLogger(__name__)


class JobInputView(AuthenticatedView, VersionedView):
    """
    Job input and role matching endpoint.
    Phase 2 Step 1: User inputs job description and gets role matches.
    """
    
    def post(self, request):
        """Process job input and return role matches."""
        try:
            logger.info(f"JobInputView POST request received")
            logger.info(f"Request data: {request.data}")
            
            # Validate input
            job_title = request.data.get('job_title', '').strip()
            job_description = request.data.get('job_description', '').strip()
            
            logger.info(f"Extracted job_title: '{job_title}', job_description: '{job_description}'")
            
            if not job_title:
                logger.warning("Job title is missing")
                raise ValidationError("Job title is required")
            
            if not job_description:
                logger.warning("Job description is missing")
                raise ValidationError("Job description is required")
            
            # Get current user and validate industry
            logger.info("Getting user manager and user profile")
            try:
                user_manager = UserManager()
                logger.info("UserManager created successfully")
                
                # Check authentication
                auth0_user_id = self.get_auth0_user_id()
                logger.info(f"Auth0 user ID: {auth0_user_id}")
                
                if not auth0_user_id:
                    logger.error("No Auth0 user ID found")
                    return APIResponse.error(
                        message="Authentication required",
                        status_code=status.HTTP_401_UNAUTHORIZED
                    )
                
                user_profile = user_manager.get_user_profile(auth0_user_id)
                logger.info(f"User profile retrieved: {user_profile is not None}")
                
            except AttributeError as e:
                logger.error(f"Authentication error - missing user attributes: {str(e)}")
                return APIResponse.error(
                    message="Invalid authentication token",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            except Exception as e:
                logger.error(f"Error getting user profile: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                raise
            
            if not user_profile:
                logger.error("User profile not found")
                return APIResponse.error(
                    message="User not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            logger.info(f"User industry: {user_profile.industry_name}")
            if not user_profile.industry_name:
                logger.warning("User has no industry selected")
                raise ValidationError("Please complete industry selection first")
            
            # Use role manager for role matching
            logger.info("Initializing role manager")
            try:
                role_manager = RoleManager()
                logger.info("Role manager initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing role manager: {str(e)}")
                raise
            
            # Create job description object for role matching
            logger.info("Creating job description object")
            try:
                job_description_obj = JobDescription(
                    title=job_title,
                    description=job_description,
                    industry=user_profile.industry_name
                )
                logger.info(f"Job description object created: {job_description_obj.search_text[:100]}...")
            except Exception as e:
                logger.error(f"Error creating job description object: {str(e)}")
                raise
            
            # Find matching roles
            logger.info("Finding matching roles")
            try:
                matched_roles = role_manager.find_matching_roles(
                    job_description=job_description_obj,
                    industry_filter=user_profile.industry_name,
                    max_results=5
                )
                logger.info(f"Found {len(matched_roles)} matching roles")
                
                # Handle empty results gracefully
                if not matched_roles:
                    logger.info("No matching roles found, returning empty result set")
                    matched_roles = []
                    
            except Exception as e:
                logger.error(f"Error finding matching roles: {str(e)}")
                # Provide fallback empty result instead of failing
                logger.warning("Returning empty results due to search error")
                matched_roles = []
            
            # Format response
            logger.info("Formatting response")
            try:
                formatted_roles = []
                for i, role_match in enumerate(matched_roles):
                    logger.info(f"Processing role match {i+1}: {role_match.role.title}")
                    formatted_roles.append({
                        'id': role_match.role.id,
                        'title': role_match.role.title,
                        'description': role_match.role.description,
                        'industry_name': role_match.role.industry_name,
                        'hierarchy_level': role_match.role.hierarchy_level.value,
                        'search_keywords': role_match.role.search_keywords,
                        'relevance_score': role_match.relevance_score
                    })
                    logger.info(f"Role {i+1} formatted successfully")
                
                logger.info(f"All {len(formatted_roles)} roles formatted successfully")
            except Exception as e:
                logger.error(f"Error formatting roles: {str(e)}")
                raise
            
            response_data = {
                'user_job_input': {
                    'job_title': job_title,
                    'job_description': job_description,
                    'user_industry': user_profile.industry_name
                },
                'matched_roles': formatted_roles,
                'total_matches': len(formatted_roles)
            }
            
            logger.info("Returning successful response")
            return APIResponse.success(data=response_data)
            
        except (ValidationError, BusinessLogicError) as e:
            logger.error(f"Validation/Business logic error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in JobInputView: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return APIResponse.error(
                message="Job input processing failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                    status_code=status.HTTP_404_NOT_FOUND
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
                status_code=status.HTTP_201_CREATED
            )
            
        except (ValidationError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error(f"New role creation error: {str(e)}")
            return APIResponse.error(
                message="New role creation failed",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                    'relevance_score': role_match.relevance_score
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
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )