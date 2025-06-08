"""
Onboarding session-related domain events.
These events track the onboarding process lifecycle.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field

from domains.shared.events.base_event import DomainEvent


class OnboardingSessionStartedEvent(DomainEvent):
    """Event raised when a user starts the onboarding process."""
    
    user_id: str
    session_id: str
    session_type: str = "full"  # full, quick, guided
    expected_duration_minutes: int = 15
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.session_started",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingStepCompletedEvent(DomainEvent):
    """Event raised when a user completes an onboarding step."""
    
    user_id: str
    session_id: str
    step_name: str
    step_data: Dict[str, Any]
    completion_time_seconds: Optional[int] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.step_completed",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingStepSkippedEvent(DomainEvent):
    """Event raised when a user skips an onboarding step."""
    
    user_id: str
    session_id: str
    step_name: str
    skip_reason: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.step_skipped",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingSessionPausedEvent(DomainEvent):
    """Event raised when a user pauses the onboarding process."""
    
    user_id: str
    session_id: str
    current_step: str
    pause_reason: str = "user_initiated"  # user_initiated, session_timeout, technical_issue
    progress_percentage: float
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.session_paused",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingSessionResumedEvent(DomainEvent):
    """Event raised when a user resumes a paused onboarding session."""
    
    user_id: str
    session_id: str
    resumed_at_step: str
    pause_duration_minutes: int
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.session_resumed",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingSessionCompletedEvent(DomainEvent):
    """Event raised when a user completes the entire onboarding process."""
    
    user_id: str = Field(..., description="Unique identifier of the user who completed onboarding")
    session_id: str = Field(..., description="Unique identifier of the onboarding session")
    total_duration_minutes: int = Field(..., description="Total time spent on onboarding in minutes")
    completed_steps: List[str] = Field(..., description="List of completed onboarding steps")
    skipped_steps: List[str] = Field(..., description="List of skipped onboarding steps")
    completion_rate: float = Field(..., description="Percentage of steps completed (0.0 to 100.0)")
    final_user_profile: Optional[Dict[str, Any]] = Field(default=None, description="Final user profile data after onboarding")
    event_type: str = Field(default="onboarding.session_completed", description="Type of the event")
    
    def __init__(self, **data):
        # Set aggregate_id to session_id if not provided
        if 'aggregate_id' not in data and 'session_id' in data:
            data['aggregate_id'] = data['session_id']
        super().__init__(**data)


class OnboardingSessionAbandonedEvent(DomainEvent):
    """Event raised when a user abandons the onboarding process."""
    
    user_id: str
    session_id: str
    last_completed_step: Optional[str] = None
    abandonment_point: str
    session_duration_minutes: int
    progress_percentage: float
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.session_abandoned",
            aggregate_id=data.get('session_id'),
            **data
        )


class OnboardingSessionExpiredEvent(DomainEvent):
    """Event raised when an onboarding session expires."""
    
    user_id: str
    session_id: str
    current_step: str
    progress_percentage: float
    
    def __init__(self, **data):
        super().__init__(
            event_type="onboarding.session_expired",
            aggregate_id=data.get('session_id'),
            **data
        )