from core.patterns.mapper import Mapper
from domains.onboarding.models.onboarding_session import OnboardingSession, OnboardingStep
from domains.onboarding.dto.responses import OnboardingSessionResponse, OnboardingStepResponse

class OnboardingStepMapper(Mapper[OnboardingStep, OnboardingStepResponse]):
    """Maps onboarding steps"""
    
    def to_dto(self, model: OnboardingStep) -> OnboardingStepResponse:
        return OnboardingStepResponse(
            step_id=model.step_id,
            name=model.name,
            status=model.status.value,
            completed_at=model.completed_at,
            data=model.data
        )
    
    def to_model(self, dto: OnboardingStepResponse) -> OnboardingStep:
        # Note: This is a simplified mapping
        step = OnboardingStep(
            step_id=dto.step_id,
            phase=None,  # Would need additional info
            name=dto.name,
            description=""  # Would need additional info
        )
        step.completed_at = dto.completed_at
        step.data = dto.data
        return step

class OnboardingSessionMapper(Mapper[OnboardingSession, OnboardingSessionResponse]):
    """Maps onboarding session with nested steps"""
    
    def __init__(self, step_mapper: OnboardingStepMapper):
        self.step_mapper = step_mapper
    
    def to_dto(self, model: OnboardingSession) -> OnboardingSessionResponse:
        return OnboardingSessionResponse(
            session_id=model.id,
            user_id=model.user_id,
            status=model.current_phase.value,
            current_step=model.current_step.step_id if model.current_step else None,
            progress_percentage=self._calculate_progress(model),
            steps=self.step_mapper.to_dto_list(model.steps),
            started_at=model.started_at or model.created_at,
            completed_at=model.completed_at,
            metadata={}
        )
    
    def to_model(self, dto: OnboardingSessionResponse) -> OnboardingSession:
        # Note: This is a simplified mapping back
        session = OnboardingSession(
            user_id=dto.user_id,
            started_at=dto.started_at,
            completed_at=dto.completed_at
        )
        session.id = dto.session_id
        return session
    
    def _calculate_progress(self, session: OnboardingSession) -> int:
        """Calculate onboarding progress"""
        if not session.steps:
            return 0
        completed = sum(1 for step in session.steps if step.is_completed)
        return int((completed / len(session.steps)) * 100)

# Singleton instances
onboarding_step_mapper = OnboardingStepMapper()
onboarding_session_mapper = OnboardingSessionMapper(onboarding_step_mapper)