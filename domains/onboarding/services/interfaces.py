"""
Onboarding Domain Service Interfaces

Defines contracts for onboarding-related business services.
These interfaces handle user onboarding flow and related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class IOnboardingService(ABC):
    """
    Onboarding service interface for managing user onboarding process.
    
    Handles the complete onboarding workflow including profile setup,
    preferences, and initial configuration.
    """
    
    @abstractmethod
    def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Start the onboarding process for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict containing:
                - session_id: Onboarding session ID
                - current_step: Current step in process
                - total_steps: Total number of steps
                - status: Session status
        """
        pass
    
    @abstractmethod
    def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get current onboarding status for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict containing:
                - is_completed: Whether onboarding is complete
                - current_step: Current step if in progress
                - completed_steps: List of completed steps
                - remaining_steps: List of remaining steps
        """
        pass
    
    @abstractmethod
    def update_step(self, user_id: str, step_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update data for a specific onboarding step.
        
        Args:
            user_id: User's ID
            step_name: Name of the step to update
            data: Step data to save
            
        Returns:
            Dict containing:
                - success: Whether update was successful
                - next_step: Next step to complete
                - validation_errors: Any validation errors
        """
        pass
    
    @abstractmethod
    def complete_onboarding(self, user_id: str) -> bool:
        """
        Mark onboarding as complete for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if successfully completed
            
        Raises:
            OnboardingIncompleteError: If required steps are not finished
        """
        pass
    
    @abstractmethod
    def skip_onboarding(self, user_id: str, reason: Optional[str] = None) -> bool:
        """
        Skip the onboarding process.
        
        Args:
            user_id: User's ID
            reason: Optional reason for skipping
            
        Returns:
            True if successfully skipped
        """
        pass
    
    @abstractmethod
    def reset_onboarding(self, user_id: str) -> bool:
        """
        Reset onboarding progress for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if successfully reset
        """
        pass
    
    @abstractmethod
    def get_onboarding_analytics(self, 
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get onboarding analytics and metrics.
        
        Args:
            start_date: Optional start date for metrics
            end_date: Optional end date for metrics
            
        Returns:
            Dict containing analytics data
        """
        pass


class IRecommendationService(ABC):
    """
    Recommendation service interface for generating personalized recommendations.
    
    Handles role recommendations, course suggestions, and other personalized content.
    """
    
    @abstractmethod
    def get_role_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personalized role recommendations for a user.
        
        Args:
            user_id: User's ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended roles with scores
        """
        pass
    
    @abstractmethod
    def get_course_recommendations(self, user_id: str, role_id: Optional[str] = None, 
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personalized course recommendations.
        
        Args:
            user_id: User's ID
            role_id: Optional specific role to get courses for
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended courses with relevance scores
        """
        pass
    
    @abstractmethod
    def get_partner_recommendations(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get communication partner recommendations.
        
        Args:
            user_id: User's ID
            context: Optional context for recommendations
            
        Returns:
            List of recommended partners
        """
        pass
    
    @abstractmethod
    def get_unit_recommendations(self, user_id: str, partner_id: str) -> List[Dict[str, Any]]:
        """
        Get communication unit recommendations for a specific partner.
        
        Args:
            user_id: User's ID
            partner_id: Partner ID
            
        Returns:
            List of recommended units
        """
        pass
    
    @abstractmethod
    def record_recommendation_feedback(self, user_id: str, recommendation_id: str, 
                                     feedback_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record user feedback on a recommendation.
        
        Args:
            user_id: User's ID
            recommendation_id: ID of the recommendation
            feedback_type: Type of feedback (e.g., 'accepted', 'rejected', 'viewed')
            metadata: Optional additional feedback data
            
        Returns:
            True if feedback recorded successfully
        """
        pass
    
    @abstractmethod
    def get_recommendation_history(self, user_id: str, 
                                 recommendation_type: Optional[str] = None,
                                 limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recommendation history for a user.
        
        Args:
            user_id: User's ID
            recommendation_type: Optional filter by type
            limit: Maximum number of records
            
        Returns:
            List of past recommendations with feedback
        """
        pass


class IProfileSetupService(ABC):
    """
    Profile setup service interface for managing user profile configuration.
    
    Handles industry selection, role preferences, and communication needs.
    """
    
    @abstractmethod
    def set_industry(self, user_id: str, industry_id: str) -> bool:
        """
        Set user's industry.
        
        Args:
            user_id: User's ID
            industry_id: Selected industry ID
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def set_job_title(self, user_id: str, job_title: str, job_description: Optional[str] = None) -> bool:
        """
        Set user's job title and description.
        
        Args:
            user_id: User's ID
            job_title: Job title
            job_description: Optional job description
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def set_language_preferences(self, user_id: str, 
                               native_language: str,
                               target_languages: List[str],
                               proficiency_levels: Dict[str, str]) -> bool:
        """
        Set user's language preferences.
        
        Args:
            user_id: User's ID
            native_language: User's native language code
            target_languages: List of target language codes
            proficiency_levels: Dict mapping language to proficiency level
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def set_communication_partners(self, user_id: str, 
                                 partner_ids: List[str],
                                 custom_partners: Optional[List[str]] = None) -> bool:
        """
        Set user's communication partner preferences.
        
        Args:
            user_id: User's ID
            partner_ids: List of selected partner IDs
            custom_partners: Optional list of custom partner names
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def set_communication_units(self, user_id: str, 
                              partner_id: str,
                              unit_ids: List[str],
                              custom_units: Optional[List[str]] = None) -> bool:
        """
        Set communication units for a specific partner.
        
        Args:
            user_id: User's ID
            partner_id: Partner ID
            unit_ids: List of selected unit IDs
            custom_units: Optional list of custom unit names
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def set_learning_goals(self, user_id: str, goals: List[Dict[str, Any]]) -> bool:
        """
        Set user's learning goals.
        
        Args:
            user_id: User's ID
            goals: List of learning goals with priorities
            
        Returns:
            True if successfully set
        """
        pass
    
    @abstractmethod
    def validate_profile_completeness(self, user_id: str) -> Dict[str, Any]:
        """
        Validate if user profile is complete.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict containing:
                - is_complete: Whether profile is complete
                - missing_fields: List of missing required fields
                - completion_percentage: Profile completion percentage
        """
        pass