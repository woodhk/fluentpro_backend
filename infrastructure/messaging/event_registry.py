from infrastructure.messaging.event_bus import IEventBus
from domains.authentication.events.user_events import UserRegisteredEvent, UserLoggedInEvent
from domains.onboarding.events.session_events import OnboardingSessionCompletedEvent

async def register_event_handlers(event_bus: IEventBus):
    """Register all event handlers"""
    
    # Authentication events trigger onboarding
    from domains.onboarding.events.handlers import handle_user_registered
    event_bus.subscribe(UserRegisteredEvent, handle_user_registered)
    
    # Onboarding events trigger notifications
    from domains.authentication.events.handlers import handle_onboarding_completed
    event_bus.subscribe(OnboardingSessionCompletedEvent, handle_onboarding_completed)