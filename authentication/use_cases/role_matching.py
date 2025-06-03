"""
Use case for role matching and custom role creation.
"""

from typing import Dict, Any, List, Optional
import logging

from core.exceptions import ValidationError, BusinessLogicError, SupabaseUserNotFoundError
from authentication.models.role import (
    JobDescription, RoleMatch, Role, HierarchyLevel, 
    RoleSource, UserRoleSelection
)
from authentication.models.user import OnboardingStatus
from authentication.business.role_manager import RoleManager
from authentication.business.user_manager import UserManager

logger = logging.getLogger(__name__)


class RoleMatchingUseCase:
    """
    Use case for role matching, selection, and custom role creation.
    Orchestrates the complete role selection process including AI-powered matching.
    """
    
    def __init__(
        self,
        role_manager: Optional[RoleManager] = None,
        user_manager: Optional[UserManager] = None
    ):
        self.role_manager = role_manager or RoleManager()
        self.user_manager = user_manager or UserManager()
    
    def find_matching_roles(
        self,
        auth0_id: str,
        job_title: str,
        job_description: str,
        hierarchy_level: str = "associate"
    ) -> Dict[str, Any]:
        """
        Find roles that match user's job description.
        
        Args:
            auth0_id: User's Auth0 ID
            job_title: User's job title
            job_description: User's job description
            hierarchy_level: Job hierarchy level
            
        Returns:
            Dictionary with matched roles and user context
            
        Raises:
            ValidationError: If input data is invalid
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If matching process fails
        """
        try:
            logger.info(f"Starting role matching for user: {auth0_id}")
            
            # Step 1: Validate input
            if not job_title.strip():
                raise ValidationError("Job title is required")
            
            if not job_description.strip():
                raise ValidationError("Job description is required")
            
            # Validate hierarchy level
            try:
                hierarchy_enum = HierarchyLevel(hierarchy_level)
            except ValueError:
                valid_levels = [level.value for level in HierarchyLevel]
                raise ValidationError(
                    f"Invalid hierarchy level. Must be one of: {', '.join(valid_levels)}"
                )
            
            # Step 2: Get user profile to check industry
            user_profile = self.user_manager.get_user_profile(auth0_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(auth0_id)
            
            if not user_profile.industry_id:
                raise ValidationError("User must select an industry before role matching")
            
            # Step 3: Create job description object
            job_desc = JobDescription(
                title=job_title.strip(),
                description=job_description.strip(),
                industry=user_profile.industry_name,
                hierarchy_level=hierarchy_enum
            )
            
            # Step 4: Find matching roles
            role_matches = self.role_manager.find_matching_roles(
                job_description=job_desc,
                industry_filter=user_profile.industry_name,
                max_results=5
            )
            
            # Step 5: Prepare response with context
            response = {
                'success': True,
                'user_context': {
                    'job_title': job_title,
                    'job_description': job_description,
                    'hierarchy_level': hierarchy_level,
                    'industry': user_profile.industry_name,
                    'industry_id': user_profile.industry_id
                },
                'matched_roles': [match.to_dict() for match in role_matches],
                'match_statistics': {
                    'total_matches': len(role_matches),
                    'excellent_matches': len([m for m in role_matches if m.is_excellent_match]),
                    'good_matches': len([m for m in role_matches if m.is_good_match]),
                    'average_score': sum(m.relevance_score for m in role_matches) / len(role_matches) if role_matches else 0
                },
                'recommendations': self._generate_role_recommendations(role_matches, job_desc),
                'message': f"Found {len(role_matches)} matching roles"
            }
            
            logger.info(f"Role matching completed: {len(role_matches)} matches found")
            return response
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Role matching validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Role matching failed: {str(e)}")
            raise BusinessLogicError(f"Role matching process failed: {str(e)}")
    
    def select_existing_role(
        self,
        auth0_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """
        Select an existing role for the user.
        
        Args:
            auth0_id: User's Auth0 ID
            role_id: Selected role ID
            
        Returns:
            Dictionary with selection confirmation and user updates
            
        Raises:
            ValidationError: If role selection is invalid
            SupabaseUserNotFoundError: If user not found
        """
        try:
            logger.info(f"User {auth0_id} selecting existing role: {role_id}")
            
            # Step 1: Validate role exists
            role = self.role_manager.get_role_by_id(role_id)
            if not role:
                raise ValidationError(f"Role with ID '{role_id}' not found")
            
            if not role.is_active:
                raise ValidationError("Selected role is not available")
            
            # Step 2: Update user's selected role
            update_result = self.user_manager.update_selected_role(auth0_id, role_id)
            
            # Step 3: Record role selection for tracking
            role_selection = self.role_manager.record_role_selection(
                user_id=auth0_id,
                role_id=role_id,
                role_source=RoleSource.SELECTED,
                role_details={
                    'selected_role_title': role.title,
                    'selection_method': 'existing_role_selection'
                }
            )
            
            # Step 4: Update onboarding status
            try:
                self.user_manager.update_onboarding_status(
                    auth0_id,
                    OnboardingStatus.COMMUNICATION_NEEDS
                )
            except Exception as e:
                logger.warning(f"Failed to update onboarding status: {str(e)}")
            
            # Step 5: Get updated user profile
            user_profile = self.user_manager.get_user_profile(auth0_id)
            
            response = {
                'success': True,
                'selected_role': role.to_dict(),
                'role_source': RoleSource.SELECTED.value,
                'user_profile': user_profile.to_dict() if user_profile else None,
                'next_steps': [
                    'Select communication partners',
                    'Choose communication situations',
                    'Complete onboarding'
                ],
                'message': f"Role '{role.title}' selected successfully"
            }
            
            logger.info(f"Role selection completed for user {auth0_id}")
            return response
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Role selection failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Role selection process failed: {str(e)}")
            raise BusinessLogicError(f"Role selection failed: {str(e)}")
    
    def create_custom_role(
        self,
        auth0_id: str,
        job_title: str,
        job_description: str,
        hierarchy_level: str = "associate"
    ) -> Dict[str, Any]:
        """
        Create a custom role for the user based on their job description.
        
        Args:
            auth0_id: User's Auth0 ID
            job_title: Custom job title
            job_description: Custom job description
            hierarchy_level: Job hierarchy level
            
        Returns:
            Dictionary with created role and user updates
            
        Raises:
            ValidationError: If job data is invalid
            SupabaseUserNotFoundError: If user not found
            BusinessLogicError: If role creation fails
        """
        try:
            logger.info(f"Creating custom role for user: {auth0_id}")
            
            # Step 1: Validate input
            if not job_title.strip():
                raise ValidationError("Job title is required")
            
            if not job_description.strip():
                raise ValidationError("Job description is required")
            
            # Validate hierarchy level
            try:
                hierarchy_enum = HierarchyLevel(hierarchy_level)
            except ValueError:
                valid_levels = [level.value for level in HierarchyLevel]
                raise ValidationError(
                    f"Invalid hierarchy level. Must be one of: {', '.join(valid_levels)}"
                )
            
            # Step 2: Get user profile
            user_profile = self.user_manager.get_user_profile(auth0_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(auth0_id)
            
            if not user_profile.industry_id:
                raise ValidationError("User must select an industry before creating a role")
            
            # Step 3: Create job description object
            job_desc = JobDescription(
                title=job_title.strip(),
                description=job_description.strip(),
                industry=user_profile.industry_name,
                hierarchy_level=hierarchy_enum
            )
            
            # Step 4: Create custom role
            custom_role = self.role_manager.create_custom_role(
                job_description=job_desc,
                industry_id=user_profile.industry_id,
                created_by_user_id=user_profile.user.id
            )
            
            # Step 5: Select the newly created role for the user
            update_result = self.user_manager.update_selected_role(auth0_id, custom_role.id)
            
            # Step 6: Record role creation for tracking
            role_selection = self.role_manager.record_role_selection(
                user_id=auth0_id,
                role_id=custom_role.id,
                role_source=RoleSource.CREATED,
                role_details={
                    'created_role_title': custom_role.title,
                    'original_description': job_description,
                    'rewritten_description': custom_role.description,
                    'generated_keywords': custom_role.search_keywords,
                    'creation_method': 'custom_role_creation'
                }
            )
            
            # Step 7: Update onboarding status
            try:
                self.user_manager.update_onboarding_status(
                    auth0_id,
                    OnboardingStatus.COMMUNICATION_NEEDS
                )
            except Exception as e:
                logger.warning(f"Failed to update onboarding status: {str(e)}")
            
            # Step 8: Get updated user profile
            updated_profile = self.user_manager.get_user_profile(auth0_id)
            
            response = {
                'success': True,
                'created_role': custom_role.to_dict(),
                'role_source': RoleSource.CREATED.value,
                'user_profile': updated_profile.to_dict() if updated_profile else None,
                'ai_enhancements': {
                    'original_description': job_description,
                    'rewritten_description': custom_role.description,
                    'generated_keywords': custom_role.search_keywords,
                    'description_enhanced': custom_role.description != job_description
                },
                'next_steps': [
                    'Select communication partners',
                    'Choose communication situations', 
                    'Complete onboarding'
                ],
                'message': f"Custom role '{custom_role.title}' created and selected successfully"
            }
            
            logger.info(f"Custom role creation completed for user {auth0_id}")
            return response
            
        except (ValidationError, SupabaseUserNotFoundError) as e:
            logger.warning(f"Custom role creation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Custom role creation process failed: {str(e)}")
            raise BusinessLogicError(f"Custom role creation failed: {str(e)}")
    
    def get_role_suggestions(self, auth0_id: str, query: str = "") -> Dict[str, Any]:
        """
        Get role suggestions for a user based on their industry and optional query.
        
        Args:
            auth0_id: User's Auth0 ID
            query: Optional search query for filtering roles
            
        Returns:
            Dictionary with role suggestions
        """
        try:
            # Get user profile
            user_profile = self.user_manager.get_user_profile(auth0_id)
            if not user_profile:
                raise SupabaseUserNotFoundError(auth0_id)
            
            if not user_profile.industry_id:
                return {
                    'success': False,
                    'message': 'User must select an industry first',
                    'suggestions': []
                }
            
            # Get roles for user's industry
            industry_roles = self.role_manager.get_all_roles_for_industry(user_profile.industry_id)
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                industry_roles = [
                    role for role in industry_roles
                    if (query_lower in role.title.lower() or 
                        query_lower in role.description.lower() or
                        any(keyword.lower().startswith(query_lower) for keyword in role.search_keywords))
                ]
            
            # Limit to top suggestions
            suggestions = industry_roles[:10]
            
            return {
                'success': True,
                'user_industry': user_profile.industry_name,
                'query': query,
                'suggestions': [role.to_dict() for role in suggestions],
                'total_available': len(industry_roles),
                'message': f"Found {len(suggestions)} role suggestions"
            }
            
        except Exception as e:
            logger.error(f"Failed to get role suggestions: {str(e)}")
            raise BusinessLogicError(f"Failed to get role suggestions: {str(e)}")
    
    def _generate_role_recommendations(
        self, 
        role_matches: List[RoleMatch], 
        job_desc: JobDescription
    ) -> Dict[str, Any]:
        """
        Generate recommendations based on role matches.
        
        Args:
            role_matches: List of role matches
            job_desc: Original job description
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'action': 'review_matches',
            'message': 'Review the matched roles below',
            'tips': []
        }
        
        if not role_matches:
            recommendations.update({
                'action': 'create_custom_role',
                'message': 'No matching roles found. Consider creating a custom role.',
                'tips': [
                    'Provide more specific details about your responsibilities',
                    'Include key skills and technologies you work with',
                    'Mention the main outcomes or deliverables of your role'
                ]
            })
        elif len([m for m in role_matches if m.is_excellent_match]) > 0:
            recommendations.update({
                'action': 'select_excellent_match',
                'message': 'Excellent matches found! These roles closely align with your description.',
                'tips': [
                    'Review the top matches carefully',
                    'Consider the role descriptions and requirements',
                    'Select the role that best fits your actual responsibilities'
                ]
            })
        elif len([m for m in role_matches if m.is_good_match]) > 0:
            recommendations.update({
                'action': 'review_good_matches',
                'message': 'Good matches found. Review them or consider creating a custom role.',
                'tips': [
                    'Check if any role matches your core responsibilities',
                    'Consider adapting one of the suggestions',
                    'You can always create a custom role if none fit perfectly'
                ]
            })
        else:
            recommendations.update({
                'action': 'consider_custom_role',
                'message': 'Some matches found, but they may not be perfect fits.',
                'tips': [
                    'Review the matches to see if any are close enough',
                    'Consider creating a custom role for a perfect fit',
                    'Make sure your job description includes specific details'
                ]
            })
        
        return recommendations