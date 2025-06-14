import pytest
from uuid import uuid4
from pydantic import ValidationError
from src.schemas.onboarding.part_2 import (
    CommunicationPartner,
    GetCommunicationPartnersResponse,
    SelectCommunicationPartnersRequest,
    SelectSituationsRequest,
    OnboardingPart2SummaryResponse
)


class TestCommunicationPartnerSchema:
    """Test communication partner schema."""
    
    def test_partner_schema_valid(self):
        """Test valid partner schema creation."""
        # This will FAIL initially
        partner_id = uuid4()
        partner = CommunicationPartner(
            id=partner_id,
            name="Clients",
            description="External clients"
        )
        
        assert partner.id == partner_id
        assert partner.name == "Clients"
        assert partner.description == "External clients"
    
    def test_partner_schema_optional_description(self):
        """Test partner with no description."""
        # This will FAIL initially
        partner = CommunicationPartner(
            id=uuid4(),
            name="Colleagues"
        )
        
        assert partner.description is None


class TestGetCommunicationPartnersResponse:
    """Test get partners response schema."""
    
    def test_response_with_partners(self):
        """Test response with list of partners."""
        # This will FAIL initially
        partners = [
            CommunicationPartner(id=uuid4(), name="Clients"),
            CommunicationPartner(id=uuid4(), name="Colleagues")
        ]
        
        response = GetCommunicationPartnersResponse(
            success=True,
            message="Partners retrieved",
            partners=partners
        )
        
        assert response.success == True
        assert len(response.partners) == 2
        assert response.partners[0].name == "Clients"


class TestSelectCommunicationPartnersRequest:
    """Test partner selection request schema."""
    
    def test_valid_selection_request(self):
        """Test valid partner selection."""
        # This will FAIL initially
        partner_ids = [uuid4(), uuid4(), uuid4()]
        
        request = SelectCommunicationPartnersRequest(
            partner_ids=partner_ids
        )
        
        assert len(request.partner_ids) == 3
    
    def test_empty_selection_invalid(self):
        """Test empty selection is invalid."""
        # This will FAIL initially
        with pytest.raises(ValidationError) as exc_info:
            SelectCommunicationPartnersRequest(partner_ids=[])
        
        # Check that the error mentions minimum items
        assert "at least 1 item" in str(exc_info.value).lower()


class TestSelectSituationsRequest:
    """Test situation selection request schema."""
    
    def test_valid_situation_selection(self):
        """Test valid situation selection."""
        # This will FAIL initially
        partner_id = uuid4()
        situation_ids = [uuid4(), uuid4()]
        
        request = SelectSituationsRequest(
            partner_id=partner_id,
            situation_ids=situation_ids
        )
        
        assert request.partner_id == partner_id
        assert len(request.situation_ids) == 2
    
    def test_situation_selection_validation(self):
        """Test situation selection requires at least one."""
        # This will FAIL initially
        with pytest.raises(ValidationError):
            SelectSituationsRequest(
                partner_id=uuid4(),
                situation_ids=[]  # Empty list should fail
            )


class TestOnboardingPart2Summary:
    """Test summary response schema."""
    
    def test_summary_response(self):
        """Test complete summary response."""
        # This will FAIL initially
        selections = [
            {
                "partner": {
                    "id": str(uuid4()),
                    "name": "Clients"
                },
                "priority": 1,
                "situations": [
                    {
                        "unit": {
                            "id": str(uuid4()),
                            "name": "Meetings"
                        },
                        "priority": 1
                    }
                ]
            }
        ]
        
        response = OnboardingPart2SummaryResponse(
            success=True,
            message="Summary retrieved",
            total_partners_selected=1,
            total_situations_selected=1,
            selections=selections
        )
        
        assert response.total_partners_selected == 1
        assert response.total_situations_selected == 1
        assert len(response.selections) == 1