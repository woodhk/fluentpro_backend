"""
Integration tests for event-driven workflows across domains.
Tests cross-domain event publishing, handling, and workflow coordination.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock

from domains.shared.events.base_event import DomainEvent
from domains.shared.events.publisher import EventPublisher
from domains.shared.events.registry import EventRegistry
from domains.authentication.events.user_events import UserRegisteredEvent, UserAuthenticatedEvent
from domains.authentication.events.session_events import SessionStartedEvent, SessionEndedEvent
from domains.onboarding.events.preference_events import (
    LanguageSelectedEvent, IndustrySelectedEvent, PartnersSelectedEvent
)
from domains.onboarding.events.session_events import (
    OnboardingStartedEvent, OnboardingStepCompletedEvent, OnboardingCompletedEvent
)
from domains.authentication.use_cases.register_user import RegisterUserUseCase
from domains.authentication.dto.requests import SignupRequest
from domains.onboarding.use_cases.start_onboarding_session import StartOnboardingSessionUseCase
from domains.onboarding.use_cases.select_native_language import SelectNativeLanguageUseCase
from domains.onboarding.dto.requests import StartOnboardingRequest, SelectNativeLanguageRequest
from tests.mocks.repositories import MockUserRepository, MockIndustryRepository
from tests.mocks.services import MockAuthenticationService


class MockEventHandler:
    """Mock event handler for testing event processing."""
    
    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        self.handled_events: List[DomainEvent] = []
        self.processing_delay = 0.01
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle an event and record it."""
        await asyncio.sleep(self.processing_delay)
        self.handled_events.append(event)
        print(f"Handler {self.handler_name} processed {event.__class__.__name__}")
    
    def get_events_by_type(self, event_type: type) -> List[DomainEvent]:
        """Get all handled events of a specific type."""
        return [event for event in self.handled_events if isinstance(event, event_type)]
    
    def clear_events(self):
        """Clear handled events list."""
        self.handled_events.clear()


class MockEventPublisher(EventPublisher):
    """Mock event publisher for testing."""
    
    def __init__(self):
        super().__init__()
        self.published_events: List[DomainEvent] = []
        self.handlers: Dict[type, List[MockEventHandler]] = {}
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event and notify all handlers."""
        self.published_events.append(event)
        
        # Notify handlers for this event type
        event_type = type(event)
        if event_type in self.handlers:
            tasks = []
            for handler in self.handlers[event_type]:
                tasks.append(handler.handle(event))
            
            if tasks:
                await asyncio.gather(*tasks)
    
    def subscribe(self, event_type: type, handler: MockEventHandler) -> None:
        """Subscribe handler to event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def get_published_events(self, event_type: type = None) -> List[DomainEvent]:
        """Get published events, optionally filtered by type."""
        if event_type is None:
            return self.published_events.copy()
        return [event for event in self.published_events if isinstance(event, event_type)]
    
    def clear_events(self):
        """Clear published events list."""
        self.published_events.clear()


class TestEventDrivenWorkflows:
    """Test event-driven workflows across domains."""

    @pytest.mark.asyncio
    async def test_user_registration_triggers_onboarding_workflow(self):
        """Test that user registration automatically triggers onboarding workflow."""
        # Arrange
        event_publisher = MockEventPublisher()
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()
        
        # Set up event handlers
        onboarding_handler = MockEventHandler("OnboardingWorkflowHandler")
        notification_handler = MockEventHandler("NotificationHandler")
        analytics_handler = MockEventHandler("AnalyticsHandler")
        
        # Subscribe handlers to user events
        event_publisher.subscribe(UserRegisteredEvent, onboarding_handler)
        event_publisher.subscribe(UserRegisteredEvent, notification_handler)
        event_publisher.subscribe(UserRegisteredEvent, analytics_handler)
        
        # Configure authentication service
        auth_service.authenticate = lambda email, password: {
            "access_token": "test-token",
            "refresh_token": "test-refresh",
            "expires_in": 3600
        }
        
        # Create use case with event publisher
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        # ACT - Register user
        signup_request = SignupRequest(
            email="workflow@test.com",
            password="WorkflowPass123!",
            full_name="Workflow Test User"
        )
        
        registration_response = await register_use_case.execute(signup_request)
        
        # Allow event processing to complete
        await asyncio.sleep(0.1)
        
        # ASSERT - Verify event was published
        user_registered_events = event_publisher.get_published_events(UserRegisteredEvent)
        assert len(user_registered_events) == 1
        
        user_event = user_registered_events[0]
        assert user_event.user_id == registration_response.user.id
        assert user_event.email == "workflow@test.com"
        assert user_event.full_name == "Workflow Test User"
        
        # Verify all handlers received the event
        assert len(onboarding_handler.handled_events) == 1
        assert len(notification_handler.handled_events) == 1
        assert len(analytics_handler.handled_events) == 1
        
        # Verify event data in handlers
        for handler in [onboarding_handler, notification_handler, analytics_handler]:
            handled_event = handler.handled_events[0]
            assert isinstance(handled_event, UserRegisteredEvent)
            assert handled_event.user_id == registration_response.user.id

    @pytest.mark.asyncio
    async def test_onboarding_step_completion_event_chain(self):
        """Test event chain when completing onboarding steps."""
        # Arrange
        event_publisher = MockEventPublisher()
        user_repository = MockUserRepository()
        
        # Set up handlers for different events
        step_completion_handler = MockEventHandler("StepCompletionHandler")
        progress_tracker_handler = MockEventHandler("ProgressTrackerHandler")
        recommendation_handler = MockEventHandler("RecommendationHandler")
        
        # Subscribe to various onboarding events
        event_publisher.subscribe(OnboardingStartedEvent, step_completion_handler)
        event_publisher.subscribe(OnboardingStepCompletedEvent, progress_tracker_handler)
        event_publisher.subscribe(LanguageSelectedEvent, recommendation_handler)
        
        # Create test user
        user_id = "event-chain-user"
        user_repository._users[user_id] = {
            "id": user_id,
            "email": "chain@test.com",
            "full_name": "Event Chain User",
            "auth0_id": "auth0|chain123"
        }
        
        # Create use cases with event publisher
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        select_language_use_case = SelectNativeLanguageUseCase(
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        # ACT - Execute onboarding workflow
        # Step 1: Start onboarding
        start_request = StartOnboardingRequest(user_id=user_id)
        start_response = await start_onboarding_use_case.execute(start_request)
        
        # Step 2: Select language
        language_request = SelectNativeLanguageRequest(
            user_id=user_id,
            language_code="es"
        )
        language_response = await select_language_use_case.execute(language_request)
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        # ASSERT - Verify event chain
        # Check OnboardingStarted event
        onboarding_started_events = event_publisher.get_published_events(OnboardingStartedEvent)
        assert len(onboarding_started_events) == 1
        assert onboarding_started_events[0].user_id == user_id
        
        # Check step completion events
        step_completed_events = event_publisher.get_published_events(OnboardingStepCompletedEvent)
        assert len(step_completed_events) >= 1
        
        # Check language selection event
        language_events = event_publisher.get_published_events(LanguageSelectedEvent)
        assert len(language_events) == 1
        assert language_events[0].user_id == user_id
        assert language_events[0].language_code == "es"
        
        # Verify handlers processed events
        assert len(step_completion_handler.handled_events) >= 1
        assert len(progress_tracker_handler.handled_events) >= 1
        assert len(recommendation_handler.handled_events) == 1

    @pytest.mark.asyncio
    async def test_cross_domain_event_coordination(self):
        """Test coordination between authentication and onboarding domain events."""
        # Arrange
        event_publisher = MockEventPublisher()
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()
        
        # Cross-domain workflow coordinator
        class WorkflowCoordinator:
            def __init__(self):
                self.workflow_state = {}
            
            async def handle_user_registered(self, event: UserRegisteredEvent):
                """Handle user registration by preparing onboarding."""
                self.workflow_state[event.user_id] = {
                    "registration_completed": True,
                    "onboarding_ready": True,
                    "registration_timestamp": event.occurred_at
                }
            
            async def handle_onboarding_started(self, event: OnboardingStartedEvent):
                """Handle onboarding start by updating workflow state."""
                if event.user_id in self.workflow_state:
                    self.workflow_state[event.user_id].update({
                        "onboarding_started": True,
                        "onboarding_timestamp": event.occurred_at
                    })
            
            async def handle_session_events(self, event):
                """Handle session-related events."""
                if hasattr(event, 'user_id') and event.user_id in self.workflow_state:
                    if isinstance(event, SessionStartedEvent):
                        self.workflow_state[event.user_id]["session_active"] = True
                    elif isinstance(event, SessionEndedEvent):
                        self.workflow_state[event.user_id]["session_active"] = False
        
        coordinator = WorkflowCoordinator()
        
        # Set up coordinator as event handler
        coordinator_handler = MockEventHandler("WorkflowCoordinator")
        coordinator_handler.handle = lambda event: coordinator.handle_user_registered(event) if isinstance(event, UserRegisteredEvent) else coordinator.handle_onboarding_started(event) if isinstance(event, OnboardingStartedEvent) else coordinator.handle_session_events(event)
        
        # Subscribe coordinator to multiple event types
        event_publisher.subscribe(UserRegisteredEvent, coordinator_handler)
        event_publisher.subscribe(OnboardingStartedEvent, coordinator_handler)
        event_publisher.subscribe(SessionStartedEvent, coordinator_handler)
        event_publisher.subscribe(SessionEndedEvent, coordinator_handler)
        
        # Configure authentication
        auth_service.authenticate = lambda email, password: {
            "access_token": "coordination-token",
            "refresh_token": "coordination-refresh",
            "expires_in": 3600
        }
        
        # Create use cases
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        # ACT - Execute cross-domain workflow
        # Register user
        signup_request = SignupRequest(
            email="coordination@test.com",
            password="CoordinationPass123!",
            full_name="Coordination Test User"
        )
        registration_response = await register_use_case.execute(signup_request)
        user_id = registration_response.user.id
        
        # Simulate session start
        session_event = SessionStartedEvent(
            user_id=user_id,
            session_id="session-123",
            occurred_at=datetime.now()
        )
        await event_publisher.publish(session_event)
        
        # Start onboarding
        start_request = StartOnboardingRequest(user_id=user_id)
        onboarding_response = await start_onboarding_use_case.execute(start_request)
        
        # Simulate session end
        session_end_event = SessionEndedEvent(
            user_id=user_id,
            session_id="session-123",
            occurred_at=datetime.now()
        )
        await event_publisher.publish(session_end_event)
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        # ASSERT - Verify cross-domain coordination
        assert user_id in coordinator.workflow_state
        user_state = coordinator.workflow_state[user_id]
        
        assert user_state["registration_completed"] is True
        assert user_state["onboarding_ready"] is True
        assert user_state["onboarding_started"] is True
        assert user_state.get("session_active") is False  # Session ended
        
        # Verify all expected events were published
        assert len(event_publisher.get_published_events(UserRegisteredEvent)) == 1
        assert len(event_publisher.get_published_events(OnboardingStartedEvent)) == 1
        assert len(event_publisher.get_published_events(SessionStartedEvent)) == 1
        assert len(event_publisher.get_published_events(SessionEndedEvent)) == 1

    @pytest.mark.asyncio
    async def test_event_handling_failure_resilience(self):
        """Test that event-driven workflows are resilient to handler failures."""
        # Arrange
        event_publisher = MockEventPublisher()
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()
        
        # Create handlers with different failure behaviors
        reliable_handler = MockEventHandler("ReliableHandler")
        
        class FailingHandler(MockEventHandler):
            def __init__(self, name: str, failure_rate: float = 0.5):
                super().__init__(name)
                self.failure_rate = failure_rate
                self.call_count = 0
            
            async def handle(self, event: DomainEvent) -> None:
                self.call_count += 1
                if self.call_count % 2 == 0:  # Fail every other call
                    raise Exception(f"Handler {self.handler_name} failed")
                await super().handle(event)
        
        failing_handler = FailingHandler("FailingHandler")
        
        # Subscribe both handlers
        event_publisher.subscribe(UserRegisteredEvent, reliable_handler)
        event_publisher.subscribe(UserRegisteredEvent, failing_handler)
        
        # Override publish method to handle failures gracefully
        original_publish = event_publisher.publish
        
        async def resilient_publish(event: DomainEvent) -> None:
            self = event_publisher
            self.published_events.append(event)
            
            event_type = type(event)
            if event_type in self.handlers:
                # Process handlers and collect failures
                failed_handlers = []
                successful_handlers = []
                
                for handler in self.handlers[event_type]:
                    try:
                        await handler.handle(event)
                        successful_handlers.append(handler.handler_name)
                    except Exception as e:
                        failed_handlers.append((handler.handler_name, str(e)))
                
                # Log failures but don't stop processing
                if failed_handlers:
                    print(f"Event processing failures: {failed_handlers}")
                    print(f"Successful handlers: {successful_handlers}")
        
        event_publisher.publish = resilient_publish
        
        # Configure authentication
        auth_service.authenticate = lambda email, password: {
            "access_token": "resilience-token",
            "refresh_token": "resilience-refresh",
            "expires_in": 3600
        }
        
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository,
            event_publisher=event_publisher
        )
        
        # ACT - Register multiple users to test failure handling
        user_emails = ["resilient1@test.com", "resilient2@test.com", "resilient3@test.com"]
        
        for email in user_emails:
            signup_request = SignupRequest(
                email=email,
                password="ResilientPass123!",
                full_name=f"Resilient User {email.split('@')[0]}"
            )
            
            # This should succeed even if one handler fails
            registration_response = await register_use_case.execute(signup_request)
            assert registration_response.user.email == email
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        # ASSERT - Verify resilience
        # All events should have been published
        assert len(event_publisher.get_published_events(UserRegisteredEvent)) == 3
        
        # Reliable handler should have processed all events
        assert len(reliable_handler.handled_events) == 3
        
        # Failing handler should have processed some events (not all due to failures)
        assert 0 < len(failing_handler.handled_events) < 3

    @pytest.mark.asyncio
    async def test_event_ordering_and_sequencing(self):
        """Test that events are processed in correct order for sequential workflows."""
        # Arrange
        event_publisher = MockEventPublisher()
        user_repository = MockUserRepository()
        
        # Create a sequence-tracking handler
        class SequenceTracker(MockEventHandler):
            def __init__(self, name: str):
                super().__init__(name)
                self.event_sequence = []
            
            async def handle(self, event: DomainEvent) -> None:
                await super().handle(event)
                self.event_sequence.append({
                    "event_type": event.__class__.__name__,
                    "timestamp": event.occurred_at,
                    "user_id": getattr(event, 'user_id', None)
                })
        
        sequence_tracker = SequenceTracker("SequenceTracker")
        
        # Subscribe to all relevant events
        event_types = [
            OnboardingStartedEvent,
            OnboardingStepCompletedEvent,
            LanguageSelectedEvent,
            IndustrySelectedEvent,
            OnboardingCompletedEvent
        ]
        
        for event_type in event_types:
            event_publisher.subscribe(event_type, sequence_tracker)
        
        # ACT - Execute sequential workflow
        user_id = "sequence-test-user"
        user_repository._users[user_id] = {
            "id": user_id,
            "email": "sequence@test.com",
            "full_name": "Sequence Test User",
            "auth0_id": "auth0|sequence123"
        }
        
        # Simulate sequential onboarding events
        events_to_publish = [
            OnboardingStartedEvent(user_id=user_id, session_id="seq-session-1"),
            LanguageSelectedEvent(user_id=user_id, language_code="en", language_name="English"),
            OnboardingStepCompletedEvent(user_id=user_id, step_name="language_selection", step_data={"language": "en"}),
            IndustrySelectedEvent(user_id=user_id, industry_id="1", industry_name="Technology"),
            OnboardingStepCompletedEvent(user_id=user_id, step_name="industry_selection", step_data={"industry": "1"}),
            OnboardingCompletedEvent(user_id=user_id, completion_data={"total_steps": 5, "completion_rate": 100.0})
        ]
        
        # Publish events in sequence with small delays
        for event in events_to_publish:
            await event_publisher.publish(event)
            await asyncio.sleep(0.01)  # Small delay to ensure ordering
        
        # Allow final processing
        await asyncio.sleep(0.1)
        
        # ASSERT - Verify sequence
        assert len(sequence_tracker.event_sequence) == len(events_to_publish)
        
        # Verify events are in correct order
        expected_sequence = [
            "OnboardingStartedEvent",
            "LanguageSelectedEvent", 
            "OnboardingStepCompletedEvent",
            "IndustrySelectedEvent",
            "OnboardingStepCompletedEvent",
            "OnboardingCompletedEvent"
        ]
        
        actual_sequence = [item["event_type"] for item in sequence_tracker.event_sequence]
        assert actual_sequence == expected_sequence
        
        # Verify timestamps are in ascending order
        timestamps = [item["timestamp"] for item in sequence_tracker.event_sequence]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], f"Event {i} occurred before event {i-1}"
        
        # Verify all events are for the same user
        user_ids = [item["user_id"] for item in sequence_tracker.event_sequence]
        assert all(uid == user_id for uid in user_ids)