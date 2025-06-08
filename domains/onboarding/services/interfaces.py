"""
Onboarding Domain Service Interfaces

Defines contracts for onboarding-related business services.
These interfaces handle user onboarding flow and related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime


class IOnboardingService(ABC):
    """
    Onboarding service interface for managing user onboarding process.
    
    Handles the complete onboarding workflow including profile setup,
    preferences, and initial configuration.
    Includes both synchronous and asynchronous methods for AI-powered onboarding optimization.
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
    
    # Async AI-powered methods for onboarding optimization
    
    @abstractmethod
    async def start_adaptive_onboarding_async(self, user_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start AI-powered adaptive onboarding based on user context.
        
        Uses machine learning to customize the onboarding flow based on user
        characteristics, goals, and predicted needs.
        
        Args:
            user_id: User's ID
            user_context: User context data for personalization
            
        Returns:
            Dict containing:
                - session_id: Onboarding session ID
                - personalized_steps: AI-customized onboarding steps
                - estimated_completion_time: AI-estimated completion time
                - difficulty_level: Recommended difficulty level
                - priority_areas: AI-identified priority areas for user
        """
        pass
    
    @abstractmethod
    async def get_dynamic_step_guidance_async(self, user_id: str, current_step: str) -> Dict[str, Any]:
        """
        Get AI-powered dynamic guidance for current onboarding step.
        
        Args:
            user_id: User's ID
            current_step: Current onboarding step
            
        Returns:
            Dict containing:
                - step_guidance: AI-generated step-specific guidance
                - personalized_tips: Personalized tips based on user profile
                - common_challenges: AI-identified common challenges for this step
                - success_strategies: Recommended strategies for success
                - estimated_time: AI-estimated time for this step
        """
        pass
    
    @abstractmethod
    async def predict_onboarding_success_async(self, user_id: str) -> Dict[str, Any]:
        """
        Predict onboarding success probability using AI analysis.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict containing:
                - success_probability: AI-predicted success probability
                - risk_factors: Identified risk factors for completion
                - intervention_recommendations: Recommended interventions
                - optimal_timeline: AI-suggested optimal timeline
                - support_needs: Predicted support needs
        """
        pass
    
    @abstractmethod
    async def generate_personalized_content_async(self, user_id: str, content_type: str) -> Dict[str, Any]:
        """
        Generate personalized onboarding content using AI.
        
        Args:
            user_id: User's ID
            content_type: Type of content to generate (tips, examples, explanations)
            
        Returns:
            Dict containing:
                - generated_content: AI-generated personalized content
                - relevance_score: Content relevance score
                - difficulty_level: Content difficulty level
                - learning_style_match: How well content matches user's learning style
        """
        pass
    
    @abstractmethod
    async def analyze_onboarding_progress_async(self, user_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream real-time analysis of onboarding progress.
        
        Args:
            user_id: User's ID
            
        Yields:
            Dict containing progress insights:
                - progress_analysis: Current progress analysis
                - bottleneck_detection: Detected bottlenecks or issues
                - next_best_action: AI-recommended next action
                - engagement_level: Current engagement level analysis
                - completion_prediction: Updated completion prediction
        """
        yield {}  # Placeholder for async iterator
    
    @abstractmethod
    async def optimize_onboarding_flow_async(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize onboarding flow based on aggregate user data and AI analysis.
        
        Args:
            analytics_data: Aggregate analytics data for optimization
            
        Returns:
            Dict containing:
                - flow_optimizations: Recommended flow optimizations
                - step_reordering: Suggested step reordering
                - content_improvements: Content improvement suggestions
                - user_segmentation: Recommended user segmentation strategies
                - success_rate_prediction: Predicted success rate improvements
        """
        pass


class IRecommendationService(ABC):
    """
    Recommendation service interface for generating personalized recommendations.
    
    Handles role recommendations, course suggestions, and other personalized content.
    Includes both synchronous and asynchronous methods for AI-powered recommendations.
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
    
    # Async AI-powered methods for enhanced recommendations
    
    @abstractmethod
    async def get_ai_role_recommendations_async(self, user_id: str, user_input: str, 
                                              context: Optional[Dict[str, Any]] = None,
                                              limit: int = 10) -> Dict[str, Any]:
        """
        Get AI-powered role recommendations with detailed analysis.
        
        Uses machine learning and natural language processing to analyze user input
        and provide highly personalized role recommendations.
        
        Args:
            user_id: User's ID
            user_input: User's job description or role requirements
            context: Optional context (skills, preferences, history)
            limit: Maximum number of recommendations
            
        Returns:
            Dict containing:
                - recommendations: List of recommended roles with AI scores
                - reasoning: AI-generated explanations for each recommendation
                - confidence_scores: Confidence levels for recommendations
                - alternative_suggestions: Alternative role paths
                - skill_gaps: Identified skill gaps and development suggestions
        """
        pass
    
    @abstractmethod
    async def get_dynamic_course_recommendations_async(self, user_id: str, 
                                                     learning_goals: List[str],
                                                     current_progress: Optional[Dict[str, Any]] = None,
                                                     limit: int = 10) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream dynamic course recommendations based on real-time learning progress.
        
        Args:
            user_id: User's ID
            learning_goals: List of learning objectives
            current_progress: Current learning progress data
            limit: Maximum number of recommendations
            
        Yields:
            Dict containing:
                - course_recommendation: Individual course recommendation
                - relevance_score: AI-calculated relevance score
                - difficulty_match: How well difficulty matches user level
                - prerequisite_analysis: Analysis of prerequisites
                - estimated_completion_time: AI-estimated completion time
        """
        yield {}  # Placeholder for async iterator
    
    @abstractmethod
    async def generate_personalized_learning_path_async(self, user_id: str, 
                                                       target_role: str,
                                                       timeline: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate AI-optimized personalized learning path.
        
        Args:
            user_id: User's ID
            target_role: Target role to prepare for
            timeline: Optional timeline in months
            
        Returns:
            Dict containing:
                - learning_path: Structured learning path with phases
                - milestone_roadmap: Key milestones and checkpoints
                - resource_recommendations: Recommended learning resources
                - skill_progression: Expected skill development progression
                - success_probability: AI-calculated success probability
                - adaptive_adjustments: Suggestions for path adjustments
        """
        pass
    
    @abstractmethod
    async def analyze_communication_needs_async(self, user_id: str, 
                                              role_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze communication needs using AI to recommend optimal partners and units.
        
        Args:
            user_id: User's ID
            role_context: Context about user's role and communication needs
            
        Returns:
            Dict containing:
                - communication_analysis: Analysis of communication requirements
                - partner_recommendations: AI-optimized partner suggestions
                - unit_recommendations: Recommended communication units by priority
                - scenario_suggestions: Practice scenario recommendations
                - difficulty_progression: Recommended difficulty progression
        """
        pass
    
    @abstractmethod
    async def predict_learning_outcomes_async(self, user_id: str, 
                                            proposed_path: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict learning outcomes for a proposed learning path using AI.
        
        Args:
            user_id: User's ID
            proposed_path: Proposed learning path to analyze
            
        Returns:
            Dict containing:
                - success_prediction: Predicted success probability
                - timeline_analysis: Analysis of proposed timeline
                - challenge_areas: Potential challenge areas
                - optimization_suggestions: AI suggestions for optimization
                - alternative_paths: Alternative learning paths
                - risk_factors: Identified risk factors
        """
        pass
    
    @abstractmethod
    async def generate_adaptive_recommendations_async(self, user_id: str, 
                                                    interaction_data: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate adaptive recommendations based on real-time user interactions.
        
        Args:
            user_id: User's ID
            interaction_data: Real-time interaction and progress data
            
        Yields:
            Dict containing adaptive recommendations:
                - recommendation_type: Type of adaptive recommendation
                - content: Recommendation content
                - trigger_reason: What triggered this recommendation
                - urgency_level: Urgency level of the recommendation
                - expected_impact: Expected impact on learning outcomes
        """
        yield {}  # Placeholder for async iterator
    
    @abstractmethod
    async def optimize_recommendation_model_async(self, feedback_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize recommendation models based on user feedback using ML.
        
        Args:
            feedback_batch: Batch of user feedback data
            
        Returns:
            Dict containing:
                - model_improvements: Improvements made to models
                - performance_metrics: Updated performance metrics
                - validation_results: Model validation results
                - deployment_status: Status of model updates
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


class IEmbeddingService(ABC):
    """Text embedding service for semantic search"""
    
    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text"""
        pass
    
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts"""
        pass


class ICompletionService(ABC):
    """LLM completion service"""
    
    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 100) -> str:
        """Generate completion for prompt"""
        pass
    
    @abstractmethod
    async def complete_with_system(self, system: str, user: str, max_tokens: int = 100) -> str:
        """Generate completion with system message"""
        pass