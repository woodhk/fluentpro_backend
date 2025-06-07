"""
Event handler registry for setting up domain event handlers.
This module provides utilities for registering event handlers with the event bus.
"""

from typing import Callable, Dict, List
import logging

from .base_event import event_bus
from domains.authentication.events import handlers as auth_handlers
from domains.onboarding.events import handlers as onboarding_handlers

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """Registry for domain event handlers."""
    
    def __init__(self):
        self._registered = False
    
    def register_all_handlers(self):
        """Register all domain event handlers with the event bus."""
        if self._registered:
            logger.warning("Event handlers already registered")
            return
        
        try:
            # Register authentication event handlers
            self._register_authentication_handlers()
            
            # Register onboarding event handlers
            self._register_onboarding_handlers()
            
            self._registered = True
            logger.info("All domain event handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register event handlers: {e}")
            raise
    
    def _register_authentication_handlers(self):
        """Register authentication domain event handlers."""
        
        # User event handlers
        event_bus.subscribe("user.registered", auth_handlers.handle_user_registered)
        event_bus.subscribe("user.logged_in", auth_handlers.handle_user_logged_in)
        event_bus.subscribe("user.logged_out", auth_handlers.handle_user_logged_out)
        event_bus.subscribe("user.profile_updated", auth_handlers.handle_user_profile_updated)
        event_bus.subscribe("user.password_changed", auth_handlers.handle_user_password_changed)
        event_bus.subscribe("user.password_reset_requested", auth_handlers.handle_user_password_reset_requested)
        event_bus.subscribe("user.account_activated", auth_handlers.handle_user_account_activated)
        
        # Session event handlers
        event_bus.subscribe("session.created", auth_handlers.handle_session_created)
        event_bus.subscribe("auth.login_attempt_failed", auth_handlers.handle_login_attempt_failed)
        event_bus.subscribe("auth.account_locked", auth_handlers.handle_account_locked)
        event_bus.subscribe("auth.suspicious_activity_detected", auth_handlers.handle_suspicious_activity_detected)
        
        logger.info("Authentication event handlers registered")
    
    def _register_onboarding_handlers(self):
        """Register onboarding domain event handlers."""
        
        # Session event handlers
        event_bus.subscribe("onboarding.session_started", onboarding_handlers.handle_onboarding_session_started)
        event_bus.subscribe("onboarding.step_completed", onboarding_handlers.handle_onboarding_step_completed)
        event_bus.subscribe("onboarding.step_skipped", onboarding_handlers.handle_onboarding_step_skipped)
        event_bus.subscribe("onboarding.session_completed", onboarding_handlers.handle_onboarding_session_completed)
        event_bus.subscribe("onboarding.session_abandoned", onboarding_handlers.handle_onboarding_session_abandoned)
        
        # Preference event handlers
        event_bus.subscribe("onboarding.language_selected", onboarding_handlers.handle_language_selected)
        event_bus.subscribe("onboarding.industry_selected", onboarding_handlers.handle_industry_selected)
        event_bus.subscribe("onboarding.role_selected", onboarding_handlers.handle_role_selected)
        event_bus.subscribe("onboarding.custom_role_created", onboarding_handlers.handle_custom_role_created)
        event_bus.subscribe("onboarding.role_match_performed", onboarding_handlers.handle_role_match_performed)
        event_bus.subscribe("onboarding.communication_partners_selected", onboarding_handlers.handle_communication_partners_selected)
        event_bus.subscribe("onboarding.partner_situations_configured", onboarding_handlers.handle_partner_situations_configured)
        event_bus.subscribe("onboarding.personalization_complete", onboarding_handlers.handle_personalization_complete)
        
        logger.info("Onboarding event handlers registered")
    
    def get_registered_handlers(self) -> Dict[str, List[Callable]]:
        """Get all registered handlers by event type."""
        handlers = {}
        for event_type in event_bus._handlers:
            handlers[event_type] = event_bus.get_handlers(event_type)
        return handlers
    
    def is_registered(self) -> bool:
        """Check if handlers are registered."""
        return self._registered


# Global registry instance
event_registry = EventHandlerRegistry()


def setup_event_handlers():
    """Convenience function to set up all event handlers."""
    event_registry.register_all_handlers()


def get_event_handlers_summary() -> Dict[str, int]:
    """Get summary of registered event handlers."""
    handlers = event_registry.get_registered_handlers()
    return {
        event_type: len(handler_list) 
        for event_type, handler_list in handlers.items()
    }