"""
Onboarding flow domain models.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum


class OnboardingPhase(Enum):
    """Phases of the onboarding process."""
    NOT_STARTED = "not_started"
    BASIC_INFO = "basic_info"           # Language selection
    INDUSTRY_SELECTION = "industry_selection"
    ROLE_SELECTION = "role_selection"
    COMMUNICATION_NEEDS = "communication_needs"  # Partners and units
    COMPLETED = "completed"


class OnboardingStepStatus(Enum):
    """Status of individual onboarding steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class OnboardingStep:
    """
    Individual step within an onboarding phase.
    """
    step_id: str
    phase: OnboardingPhase
    name: str
    description: str
    status: OnboardingStepStatus = OnboardingStepStatus.PENDING
    is_required: bool = True
    order: int = 0
    completed_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status == OnboardingStepStatus.COMPLETED
    
    @property
    def is_skippable(self) -> bool:
        """Check if step can be skipped."""
        return not self.is_required
    
    def mark_completed(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Mark step as completed."""
        self.status = OnboardingStepStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if data:
            self.data.update(data)
    
    def mark_skipped(self) -> None:
        """Mark step as skipped (only if skippable)."""
        if self.is_skippable:
            self.status = OnboardingStepStatus.SKIPPED
            self.completed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            'step_id': self.step_id,
            'phase': self.phase.value,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'is_required': self.is_required,
            'is_completed': self.is_completed,
            'is_skippable': self.is_skippable,
            'order': self.order,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'data': self.data
        }


@dataclass
class OnboardingFlow:
    """
    Complete onboarding flow for a user.
    """
    user_id: str
    current_phase: OnboardingPhase = OnboardingPhase.NOT_STARTED
    steps: List[OnboardingStep] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default steps if none provided."""
        if not self.steps:
            self.steps = self._create_default_steps()
    
    def _create_default_steps(self) -> List[OnboardingStep]:
        """Create default onboarding steps."""
        return [
            OnboardingStep(
                step_id="select_language",
                phase=OnboardingPhase.BASIC_INFO,
                name="Select Native Language",
                description="Choose your native language for personalized content",
                order=1
            ),
            OnboardingStep(
                step_id="select_industry",
                phase=OnboardingPhase.INDUSTRY_SELECTION,
                name="Select Industry",
                description="Choose your industry for relevant role suggestions",
                order=2
            ),
            OnboardingStep(
                step_id="job_input",
                phase=OnboardingPhase.ROLE_SELECTION,
                name="Describe Your Role",
                description="Provide your job title and description",
                order=3
            ),
            OnboardingStep(
                step_id="role_selection",
                phase=OnboardingPhase.ROLE_SELECTION,
                name="Select or Create Role",
                description="Choose from suggested roles or create a custom one",
                order=4
            ),
            OnboardingStep(
                step_id="select_partners",
                phase=OnboardingPhase.COMMUNICATION_NEEDS,
                name="Select Communication Partners",
                description="Choose who you communicate with at work",
                order=5
            ),
            OnboardingStep(
                step_id="select_units",
                phase=OnboardingPhase.COMMUNICATION_NEEDS,
                name="Select Communication Situations",
                description="Choose the types of communication situations you encounter",
                order=6
            )
        ]
    
    @property
    def progress_percentage(self) -> int:
        """Calculate onboarding completion percentage."""
        if not self.steps:
            return 0
        
        completed_steps = len([s for s in self.steps if s.is_completed])
        return int((completed_steps / len(self.steps)) * 100)
    
    @property
    def is_completed(self) -> bool:
        """Check if onboarding is completed."""
        return self.current_phase == OnboardingPhase.COMPLETED
    
    @property
    def current_step(self) -> Optional[OnboardingStep]:
        """Get the current step to be completed."""
        for step in sorted(self.steps, key=lambda x: x.order):
            if step.status in [OnboardingStepStatus.PENDING, OnboardingStepStatus.IN_PROGRESS]:
                return step
        return None
    
    @property
    def next_step(self) -> Optional[OnboardingStep]:
        """Get the next pending step."""
        current = self.current_step
        if not current:
            return None
        
        return current
    
    def get_steps_for_phase(self, phase: OnboardingPhase) -> List[OnboardingStep]:
        """Get all steps for a specific phase."""
        return [step for step in self.steps if step.phase == phase]
    
    def complete_step(self, step_id: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Complete a specific step.
        
        Args:
            step_id: ID of the step to complete
            data: Optional data to store with the step
            
        Returns:
            True if step was completed successfully
        """
        for step in self.steps:
            if step.step_id == step_id:
                step.mark_completed(data)
                self._update_current_phase()
                return True
        return False
    
    def skip_step(self, step_id: str) -> bool:
        """
        Skip a specific step (if skippable).
        
        Args:
            step_id: ID of the step to skip
            
        Returns:
            True if step was skipped successfully
        """
        for step in self.steps:
            if step.step_id == step_id and step.is_skippable:
                step.mark_skipped()
                self._update_current_phase()
                return True
        return False
    
    def _update_current_phase(self) -> None:
        """Update current phase based on completed steps."""
        # Check if all steps are completed
        all_required_completed = all(
            step.is_completed or (step.status == OnboardingStepStatus.SKIPPED and not step.is_required)
            for step in self.steps
        )
        
        if all_required_completed:
            self.current_phase = OnboardingPhase.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
            return
        
        # Find the highest phase with completed steps
        phase_order = list(OnboardingPhase)
        
        for phase in reversed(phase_order[1:]):  # Skip NOT_STARTED
            phase_steps = self.get_steps_for_phase(phase)
            if phase_steps and any(step.is_completed for step in phase_steps):
                # Check if all required steps in this phase are completed
                all_phase_steps_done = all(
                    step.is_completed or (not step.is_required and step.status == OnboardingStepStatus.SKIPPED)
                    for step in phase_steps
                )
                
                if all_phase_steps_done:
                    # Move to next phase if current phase is complete
                    next_phase_index = phase_order.index(phase) + 1
                    if next_phase_index < len(phase_order):
                        self.current_phase = phase_order[next_phase_index]
                    else:
                        self.current_phase = OnboardingPhase.COMPLETED
                else:
                    self.current_phase = phase
                return
        
        # If no steps completed, check if we've started
        if any(step.status == OnboardingStepStatus.IN_PROGRESS for step in self.steps):
            self.current_phase = OnboardingPhase.BASIC_INFO
        elif not self.started_at:
            self.current_phase = OnboardingPhase.NOT_STARTED
    
    def start_onboarding(self) -> None:
        """Start the onboarding process."""
        if not self.started_at:
            self.started_at = datetime.utcnow()
            self.current_phase = OnboardingPhase.BASIC_INFO
    
    def reset_onboarding(self) -> None:
        """Reset onboarding to start."""
        self.current_phase = OnboardingPhase.NOT_STARTED
        self.started_at = None
        self.completed_at = None
        
        for step in self.steps:
            step.status = OnboardingStepStatus.PENDING
            step.completed_at = None
            step.data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert onboarding flow to dictionary."""
        return {
            'user_id': self.user_id,
            'current_phase': self.current_phase.value,
            'progress_percentage': self.progress_percentage,
            'is_completed': self.is_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_step': self.current_step.to_dict() if self.current_step else None,
            'next_step': self.next_step.to_dict() if self.next_step else None,
            'steps': [step.to_dict() for step in sorted(self.steps, key=lambda x: x.order)],
            'steps_by_phase': {
                phase.value: [
                    step.to_dict() for step in self.get_steps_for_phase(phase)
                ]
                for phase in OnboardingPhase
            }
        }


@dataclass
class UserSession:
    """
    User session data for onboarding tracking.
    """
    session_id: str
    user_id: str
    phase: OnboardingPhase
    session_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Set default expiration time."""
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(days=7)
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at if self.expires_at else False
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update session data."""
        self.session_data.update(data)
        self.updated_at = datetime.utcnow()
    
    def extend_expiration(self, days: int = 7) -> None:
        """Extend session expiration."""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()
    
    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'phase': self.phase.value,
            'session_data': self.session_data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid
        }