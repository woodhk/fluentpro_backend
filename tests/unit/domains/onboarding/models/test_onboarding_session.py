import pytest
from datetime import datetime, timedelta
from domains.onboarding.models.onboarding_session import OnboardingSession
from domains.onboarding.models.communication_partner import CommunicationPartner, CommunicationUnit


class TestOnboardingSession:
    def test_create_onboarding_session(self):
        # Arrange & Act
        session = OnboardingSession(
            user_id="user-123",
            session_type="initial"
        )
        
        # Assert
        assert session.user_id == "user-123"
        assert session.session_type == "initial"
        assert session.status == "in_progress"
        assert session.id is not None
        assert session.created_at is not None
        assert session.updated_at is not None
    
    def test_session_expiration(self):
        # Arrange
        session = OnboardingSession(
            user_id="user-456",
            session_type="initial"
        )
        
        # Act
        expires_at = session.created_at + timedelta(hours=24)
        
        # Assert
        assert expires_at > datetime.utcnow()
        assert session.status == "in_progress"
    
    def test_session_data_storage(self):
        # Arrange
        session = OnboardingSession(
            user_id="user-789",
            session_type="initial"
        )
        
        # Act
        session.data = {
            "current_step": "industry_selection",
            "completed_steps": ["language_selection"],
            "preferences": {
                "native_language": "en"
            }
        }
        
        # Assert
        assert session.data["current_step"] == "industry_selection"
        assert "language_selection" in session.data["completed_steps"]
        assert session.data["preferences"]["native_language"] == "en"
    
    def test_complete_session(self):
        # Arrange
        session = OnboardingSession(
            user_id="user-999",
            session_type="initial"
        )
        
        # Act
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        
        # Assert
        assert session.status == "completed"
        assert session.completed_at is not None
        assert session.completed_at > session.created_at


class TestCommunicationPartner:
    def test_create_communication_partner(self):
        # Arrange & Act
        partner = CommunicationPartner(
            name="Senior Management",
            category="internal",
            is_active=True
        )
        
        # Assert
        assert partner.name == "Senior Management"
        assert partner.category == "internal"
        assert partner.is_active is True
        assert partner.id is not None
    
    def test_custom_communication_partner(self):
        # Arrange & Act
        partner = CommunicationPartner(
            name="Venture Capitalists",
            category="external",
            is_custom=True,
            created_by_user_id="user-123"
        )
        
        # Assert
        assert partner.name == "Venture Capitalists"
        assert partner.is_custom is True
        assert partner.created_by_user_id == "user-123"
    
    def test_partner_deactivation(self):
        # Arrange
        partner = CommunicationPartner(
            name="Suppliers",
            category="external",
            is_active=True
        )
        
        # Act
        partner.is_active = False
        
        # Assert
        assert partner.is_active is False


class TestCommunicationUnit:
    def test_create_communication_unit(self):
        # Arrange & Act
        unit = CommunicationUnit(
            name="Team Meetings",
            description="Regular team sync meetings",
            category="meeting"
        )
        
        # Assert
        assert unit.name == "Team Meetings"
        assert unit.description == "Regular team sync meetings"
        assert unit.category == "meeting"
        assert unit.id is not None
    
    def test_unit_with_partner_association(self):
        # Arrange
        partner = CommunicationPartner(
            name="Colleagues",
            category="internal"
        )
        
        # Act
        unit = CommunicationUnit(
            name="Brainstorming Sessions",
            description="Creative problem-solving meetings",
            category="meeting",
            default_partner_id=partner.id
        )
        
        # Assert
        assert unit.default_partner_id == partner.id
        assert unit.name == "Brainstorming Sessions"
    
    def test_custom_communication_unit(self):
        # Arrange & Act
        unit = CommunicationUnit(
            name="Podcast Interviews",
            description="Recording podcast episodes as a guest",
            category="presentation",
            is_custom=True,
            created_by_user_id="user-456"
        )
        
        # Assert
        assert unit.name == "Podcast Interviews"
        assert unit.is_custom is True
        assert unit.created_by_user_id == "user-456"
        assert unit.category == "presentation"