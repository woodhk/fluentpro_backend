import pytest
from src.models.enums import CommunicationPartnerType, CommunicationSituation


class TestCommunicationPartnerType:
    """Test communication partner type enum."""
    
    def test_partner_types_exist(self):
        """Test all required partner types are defined."""
        # This test will FAIL initially (RED phase)
        assert CommunicationPartnerType.CLIENTS.value == "Clients"
        assert CommunicationPartnerType.SENIOR_MANAGEMENT.value == "Senior Management"
        assert CommunicationPartnerType.SUPPLIERS.value == "Suppliers"
        assert CommunicationPartnerType.CUSTOMERS.value == "Customers"
        assert CommunicationPartnerType.COLLEAGUES.value == "Colleagues"
        assert CommunicationPartnerType.STAKEHOLDERS.value == "Stakeholders"
        assert CommunicationPartnerType.PARTNERS.value == "Partners"
    
    def test_partner_type_count(self):
        """Test we have exactly 7 partner types."""
        # This will also FAIL initially
        assert len(CommunicationPartnerType) == 7


class TestCommunicationSituation:
    """Test communication situation enum."""
    
    def test_situation_types_exist(self):
        """Test all required situation types are defined."""
        # This test will FAIL initially (RED phase)
        situations = [
            ("INTERVIEWS", "Interviews"),
            ("CONFLICT_RESOLUTION", "Conflict Resolution"),
            ("PHONE_CALLS", "Phone Calls"),
            ("ONE_ON_ONES", "One-on-Ones"),
            ("FEEDBACK_SESSIONS", "Feedback Sessions"),
            ("TEAM_DISCUSSIONS", "Team Discussions"),
            ("NEGOTIATIONS", "Negotiations"),
            ("STATUS_UPDATES", "Status Updates"),
            ("INFORMAL_CHATS", "Informal Chats"),
            ("BRIEFINGS", "Briefings"),
            ("MEETINGS", "Meetings"),
            ("PRESENTATIONS", "Presentations"),
            ("TRAINING_SESSIONS", "Training Sessions"),
            ("CLIENT_CONVERSATIONS", "Client Conversations"),
            ("VIDEO_CONFERENCES", "Video Conferences")
        ]
        
        for enum_name, expected_value in situations:
            assert hasattr(CommunicationSituation, enum_name)
            assert getattr(CommunicationSituation, enum_name).value == expected_value
    
    def test_situation_count(self):
        """Test we have exactly 15 situation types."""
        # This will FAIL initially
        assert len(CommunicationSituation) == 15