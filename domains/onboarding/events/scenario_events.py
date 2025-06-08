"""
AI scenario-related domain events for the onboarding domain.
These events track AI-powered scenario generation and processing.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field

from domains.shared.events.base_event import DomainEvent


class ScenarioGenerationRequestedEvent(DomainEvent):
    """Event raised when AI scenario generation is requested for a user."""
    
    user_id: str = Field(..., description="Unique identifier of the user requesting scenarios")
    request_id: str = Field(..., description="Unique identifier for this generation request")
    user_profile: Dict[str, Any] = Field(..., description="User profile data for scenario personalization")
    scenario_type: str = Field(..., description="Type of scenarios to generate (practice, assessment, conversation)")
    difficulty_level: str = Field(default="intermediate", description="Difficulty level (beginner, intermediate, advanced)")
    context_requirements: Dict[str, Any] = Field(default_factory=dict, description="Specific context requirements for scenarios")
    max_scenarios: int = Field(default=5, description="Maximum number of scenarios to generate")
    priority: str = Field(default="normal", description="Processing priority (low, normal, high, urgent)")
    event_type: str = Field(default="onboarding.scenario_generation_requested", description="Type of the event")
    
    def __init__(self, **data):
        # Set aggregate_id to request_id if not provided
        if 'aggregate_id' not in data and 'request_id' in data:
            data['aggregate_id'] = data['request_id']
        super().__init__(**data)


class ScenarioGenerationStartedEvent(DomainEvent):
    """Event raised when AI scenario generation begins processing."""
    
    user_id: str = Field(..., description="Unique identifier of the user")
    request_id: str = Field(..., description="Unique identifier for this generation request")
    ai_model: str = Field(..., description="AI model being used for generation")
    estimated_completion_seconds: Optional[int] = Field(default=None, description="Estimated time to completion")
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.scenario_generation_started",
            aggregate_id=data.get('request_id'),
            **data
        )


class ScenarioGenerationCompletedEvent(DomainEvent):
    """Event raised when AI scenario generation is completed successfully."""
    
    user_id: str = Field(..., description="Unique identifier of the user")
    request_id: str = Field(..., description="Unique identifier for this generation request")
    generated_scenarios: List[Dict[str, Any]] = Field(..., description="List of generated scenarios")
    generation_time_seconds: int = Field(..., description="Actual time taken for generation")
    ai_model: str = Field(..., description="AI model used for generation")
    quality_score: Optional[float] = Field(default=None, description="Quality assessment score (0.0 to 1.0)")
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.scenario_generation_completed",
            aggregate_id=data.get('request_id'),
            **data
        )


class ScenarioGenerationFailedEvent(DomainEvent):
    """Event raised when AI scenario generation fails."""
    
    user_id: str = Field(..., description="Unique identifier of the user")
    request_id: str = Field(..., description="Unique identifier for this generation request")
    error_code: str = Field(..., description="Error code indicating failure type")
    error_message: str = Field(..., description="Human-readable error message")
    retry_count: int = Field(default=0, description="Number of retry attempts made")
    max_retries: int = Field(default=3, description="Maximum number of retries allowed")
    ai_model: Optional[str] = Field(default=None, description="AI model that failed")
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.scenario_generation_failed",
            aggregate_id=data.get('request_id'),
            **data
        )


class ScenarioValidationRequestedEvent(DomainEvent):
    """Event raised when scenario validation is requested."""
    
    user_id: str = Field(..., description="Unique identifier of the user")
    request_id: str = Field(..., description="Original generation request identifier")
    scenarios: List[Dict[str, Any]] = Field(..., description="Scenarios to validate")
    validation_criteria: Dict[str, Any] = Field(..., description="Validation criteria and rules")
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.scenario_validation_requested",
            aggregate_id=data.get('request_id'),
            **data
        )


class ScenarioValidationCompletedEvent(DomainEvent):
    """Event raised when scenario validation is completed."""
    
    user_id: str = Field(..., description="Unique identifier of the user")
    request_id: str = Field(..., description="Original generation request identifier")
    validated_scenarios: List[Dict[str, Any]] = Field(..., description="Scenarios that passed validation")
    rejected_scenarios: List[Dict[str, Any]] = Field(..., description="Scenarios that failed validation")
    validation_summary: Dict[str, Any] = Field(..., description="Summary of validation results")
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.scenario_validation_completed",
            aggregate_id=data.get('request_id'),
            **data
        )