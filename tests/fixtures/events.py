"""
Event fixtures for testing domain events and messaging.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from domains.shared.events.base_event import DomainEvent
from domains.authentication.events.user_events import (
    UserRegisteredEvent, UserLoggedInEvent, UserLoggedOutEvent
)
from domains.authentication.events.session_events import (
    SessionStartedEvent, SessionEndedEvent, SessionExtendedEvent
)
from domains.onboarding.events.session_events import (
    OnboardingStartedEvent, OnboardingCompletedEvent, OnboardingProgressEvent
)
from domains.onboarding.events.preference_events import (
    LanguageSelectedEvent, IndustrySelectedEvent, RoleMatchedEvent,
    CommunicationPreferencesSetEvent
)


class EventFixtures:
    """Factory for creating test events."""
    
    @staticmethod
    def create_base_event(
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> DomainEvent:
        """Create a basic event with default values."""
        return DomainEvent(
            event_id=kwargs.get('event_id', str(uuid.uuid4())),
            aggregate_id=user_id or str(uuid.uuid4()),
            event_type=event_type,
            correlation_id=correlation_id or str(uuid.uuid4()),
            metadata={**kwargs.get('metadata', {}), 'data': data}
        )


class UserEventFixtures:
    """Fixtures for user-related events."""
    
    @staticmethod
    def create_user_created_event(
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs
    ) -> UserCreatedEvent:
        """Create a user created event."""
        return UserCreatedEvent(
            user_id=user_id or str(uuid.uuid4()),
            email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            full_name=kwargs.get('full_name', 'Test User'),
            auth0_id=kwargs.get('auth0_id', f"auth0|{uuid.uuid4()}"),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_user_updated_event(
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UserUpdatedEvent:
        """Create a user updated event."""
        return UserUpdatedEvent(
            user_id=user_id or str(uuid.uuid4()),
            changes=changes or {'full_name': 'Updated Name'},
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_user_deleted_event(
        user_id: Optional[str] = None,
        **kwargs
    ) -> UserDeletedEvent:
        """Create a user deleted event."""
        return UserDeletedEvent(
            user_id=user_id or str(uuid.uuid4()),
            reason=kwargs.get('reason', 'User requested account deletion'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_user_profile_updated_event(
        user_id: Optional[str] = None,
        profile_changes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UserProfileUpdatedEvent:
        """Create a user profile updated event."""
        return UserProfileUpdatedEvent(
            user_id=user_id or str(uuid.uuid4()),
            profile_changes=profile_changes or {
                'bio': 'Updated bio',
                'preferred_language': 'en'
            },
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_user_status_changed_event(
        user_id: Optional[str] = None,
        old_status: str = 'pending',
        new_status: str = 'completed',
        **kwargs
    ) -> UserStatusChangedEvent:
        """Create a user status changed event."""
        return UserStatusChangedEvent(
            user_id=user_id or str(uuid.uuid4()),
            old_status=old_status,
            new_status=new_status,
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )


class SessionEventFixtures:
    """Fixtures for session-related events."""
    
    @staticmethod
    def create_session_started_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> SessionStartedEvent:
        """Create a session started event."""
        return SessionStartedEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            ip_address=kwargs.get('ip_address', '192.168.1.1'),
            user_agent=kwargs.get('user_agent', 'Test Browser'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_session_ended_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> SessionEndedEvent:
        """Create a session ended event."""
        return SessionEndedEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            duration_seconds=kwargs.get('duration_seconds', 1800),
            reason=kwargs.get('reason', 'User logout'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_session_extended_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> SessionExtendedEvent:
        """Create a session extended event."""
        return SessionExtendedEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            extension_duration=kwargs.get('extension_duration', 3600),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )


class OnboardingEventFixtures:
    """Fixtures for onboarding-related events."""
    
    @staticmethod
    def create_onboarding_started_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> OnboardingStartedEvent:
        """Create an onboarding started event."""
        return OnboardingStartedEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            initial_language=kwargs.get('initial_language', 'en'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_onboarding_completed_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> OnboardingCompletedEvent:
        """Create an onboarding completed event."""
        return OnboardingCompletedEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            completion_time_seconds=kwargs.get('completion_time_seconds', 1200),
            selected_preferences=kwargs.get('selected_preferences', {
                'language': 'en',
                'industry': 'technology',
                'role': 'software_engineer'
            }),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_onboarding_progress_event(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> OnboardingProgressEvent:
        """Create an onboarding progress event."""
        return OnboardingProgressEvent(
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            current_step=kwargs.get('current_step', 'industry_selection'),
            progress_percentage=kwargs.get('progress_percentage', 40),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_language_selected_event(
        user_id: Optional[str] = None,
        language_code: str = 'en',
        **kwargs
    ) -> LanguageSelectedEvent:
        """Create a language selected event."""
        return LanguageSelectedEvent(
            user_id=user_id or str(uuid.uuid4()),
            language_code=language_code,
            language_name=kwargs.get('language_name', 'English'),
            proficiency_level=kwargs.get('proficiency_level', 'native'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_industry_selected_event(
        user_id: Optional[str] = None,
        industry_id: Optional[str] = None,
        **kwargs
    ) -> IndustrySelectedEvent:
        """Create an industry selected event."""
        return IndustrySelectedEvent(
            user_id=user_id or str(uuid.uuid4()),
            industry_id=industry_id or str(uuid.uuid4()),
            industry_name=kwargs.get('industry_name', 'Technology'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_role_matched_event(
        user_id: Optional[str] = None,
        role_id: Optional[str] = None,
        **kwargs
    ) -> RoleMatchedEvent:
        """Create a role matched event."""
        return RoleMatchedEvent(
            user_id=user_id or str(uuid.uuid4()),
            role_id=role_id or str(uuid.uuid4()),
            role_title=kwargs.get('role_title', 'Software Engineer'),
            match_score=kwargs.get('match_score', 0.95),
            match_method=kwargs.get('match_method', 'ai_embedding'),
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )
    
    @staticmethod
    def create_communication_preferences_set_event(
        user_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> CommunicationPreferencesSetEvent:
        """Create a communication preferences set event."""
        return CommunicationPreferencesSetEvent(
            user_id=user_id or str(uuid.uuid4()),
            preferences=preferences or {
                'partners': ['senior_management', 'colleagues'],
                'units': ['meetings', 'presentations', 'emails'],
                'formality_level': 'business'
            },
            correlation_id=kwargs.get('correlation_id', str(uuid.uuid4()))
        )


class EventScenarioFixtures:
    """Create complete event scenarios for testing workflows."""
    
    @staticmethod
    def create_user_registration_flow(
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[DomainEvent]:
        """Create a complete user registration event flow."""
        user_id = user_id or str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        
        return [
            UserEventFixtures.create_user_created_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            SessionEventFixtures.create_session_started_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            OnboardingEventFixtures.create_onboarding_started_event(
                user_id=user_id,
                correlation_id=correlation_id
            )
        ]
    
    @staticmethod
    def create_onboarding_completion_flow(
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[DomainEvent]:
        """Create a complete onboarding completion event flow."""
        user_id = user_id or str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        return [
            OnboardingEventFixtures.create_language_selected_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            OnboardingEventFixtures.create_industry_selected_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            OnboardingEventFixtures.create_role_matched_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            OnboardingEventFixtures.create_communication_preferences_set_event(
                user_id=user_id,
                correlation_id=correlation_id
            ),
            OnboardingEventFixtures.create_onboarding_completed_event(
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id
            ),
            UserEventFixtures.create_user_status_changed_event(
                user_id=user_id,
                old_status='in_progress',
                new_status='completed',
                correlation_id=correlation_id
            )
        ]
    
    @staticmethod
    def create_user_session_lifecycle(
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[DomainEvent]:
        """Create a complete user session lifecycle."""
        user_id = user_id or str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        return [
            SessionEventFixtures.create_session_started_event(
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id
            ),
            SessionEventFixtures.create_session_extended_event(
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id
            ),
            SessionEventFixtures.create_session_ended_event(
                user_id=user_id,
                session_id=session_id,
                correlation_id=correlation_id
            )
        ]


def create_event_batch(count: int = 10) -> List[DomainEvent]:
    """Create a batch of mixed events for bulk testing."""
    events = []
    
    for i in range(count):
        event_type = i % 4
        
        if event_type == 0:
            events.append(UserEventFixtures.create_user_created_event())
        elif event_type == 1:
            events.append(SessionEventFixtures.create_session_started_event())
        elif event_type == 2:
            events.append(OnboardingEventFixtures.create_onboarding_started_event())
        else:
            events.append(UserEventFixtures.create_user_status_changed_event())
    
    return events