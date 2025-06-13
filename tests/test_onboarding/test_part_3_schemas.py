"""Tests for Onboarding Part 3 Schemas - TDD Phase 2"""
import pytest
from uuid import UUID
from pydantic import ValidationError

from src.schemas.onboarding.part_3 import (
    RoleSummary,
    SituationSummary,
    CommunicationPartnerSummary,
    OnboardingSummary,
    OnboardingSummaryResponse,
    CompleteOnboardingResponse
)
from src.models.enums import NativeLanguage


class TestRoleSummarySchema:
    """Test cases for RoleSummary schema."""
    
    def test_role_summary_with_valid_data(self):
        """Test RoleSummary creation with valid data."""
        role_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Financial Analyst",
            "description": "Analyzes financial data",
            "is_custom": False,
            "industry_name": "Banking & Finance"
        }
        
        role = RoleSummary(**role_data)
        assert role.title == "Financial Analyst"
        assert role.is_custom is False
        assert isinstance(role.id, UUID)
    
    def test_role_summary_with_custom_role(self):
        """Test RoleSummary with custom role (no ID)."""
        role_data = {
            "id": None,
            "title": "Custom Role Title",
            "description": "Custom description",
            "is_custom": True,
            "industry_name": "Banking & Finance"
        }
        
        role = RoleSummary(**role_data)
        assert role.id is None
        assert role.is_custom is True
        assert role.title == "Custom Role Title"
    
    def test_role_summary_validation_error(self):
        """Test RoleSummary validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            RoleSummary(
                title="Test",
                # Missing required fields
            )
        
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Missing description, is_custom, industry_name


class TestSituationSummarySchema:
    """Test cases for SituationSummary schema."""
    
    def test_situation_summary_with_valid_data(self):
        """Test SituationSummary creation with valid data."""
        situation_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Meetings",
            "description": "Team meetings",
            "priority": 1
        }
        
        situation = SituationSummary(**situation_data)
        assert situation.name == "Meetings"
        assert situation.priority == 1
        assert situation.description == "Team meetings"
    
    def test_situation_summary_without_description(self):
        """Test SituationSummary with optional description."""
        situation_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Meetings",
            "priority": 1
        }
        
        situation = SituationSummary(**situation_data)
        assert situation.description is None


class TestCommunicationPartnerSummarySchema:
    """Test cases for CommunicationPartnerSummary schema."""
    
    def test_partner_summary_with_situations(self):
        """Test CommunicationPartnerSummary with nested situations."""
        situation = SituationSummary(
            id="456e7890-e89b-12d3-a456-426614174000",
            name="Meetings",
            description=None,
            priority=1
        )
        
        partner_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Clients",
            "description": "External clients",
            "priority": 1,
            "situations": [situation.dict()]
        }
        
        partner = CommunicationPartnerSummary(**partner_data)
        assert len(partner.situations) == 1
        assert partner.situations[0].name == "Meetings"
        assert isinstance(partner.situations[0], SituationSummary)
    
    def test_partner_summary_empty_situations(self):
        """Test CommunicationPartnerSummary with no situations."""
        partner_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Suppliers",
            "description": None,
            "priority": 2,
            "situations": []
        }
        
        partner = CommunicationPartnerSummary(**partner_data)
        assert len(partner.situations) == 0
        assert partner.description is None


class TestOnboardingSummarySchema:
    """Test cases for OnboardingSummary schema."""
    
    def test_onboarding_summary_complete(self):
        """Test complete OnboardingSummary creation."""
        role = RoleSummary(
            id="789e0123-e89b-12d3-a456-426614174000",
            title="Financial Analyst",
            description="Analyzes data",
            is_custom=False,
            industry_name="Banking & Finance"
        )
        
        situation = SituationSummary(
            id="012e3456-e89b-12d3-a456-426614174000",
            name="Meetings",
            priority=1
        )
        
        partner = CommunicationPartnerSummary(
            id="456e7890-e89b-12d3-a456-426614174000",
            name="Clients",
            priority=1,
            situations=[situation]
        )
        
        summary_data = {
            "native_language": NativeLanguage.ENGLISH,
            "native_language_display": "English",
            "industry_id": "123e4567-e89b-12d3-a456-426614174000",
            "industry_name": "Banking & Finance",
            "role": role.dict(),
            "communication_partners": [partner.dict()],
            "total_partners": 1,
            "total_situations": 1,
            "onboarding_status": "personalisation",
            "is_complete": False
        }
        
        summary = OnboardingSummary(**summary_data)
        assert summary.native_language == NativeLanguage.ENGLISH
        assert summary.total_partners == 1
        assert not summary.is_complete
    
    def test_onboarding_summary_response(self):
        """Test OnboardingSummaryResponse creation."""
        # Create minimal summary
        role = RoleSummary(
            title="Test Role",
            description="Test",
            is_custom=False,
            industry_name="Test Industry"
        )
        
        summary = OnboardingSummary(
            native_language=NativeLanguage.ENGLISH,
            native_language_display="English",
            industry_name="Test Industry",
            role=role,
            communication_partners=[],
            total_partners=0,
            total_situations=0,
            onboarding_status="pending",
            is_complete=False
        )
        
        response = OnboardingSummaryResponse(
            success=True,
            message="Summary retrieved",
            summary=summary
        )
        
        assert response.success is True
        assert response.message == "Summary retrieved"
        assert response.summary.native_language == NativeLanguage.ENGLISH


class TestCompleteOnboardingResponseSchema:
    """Test cases for CompleteOnboardingResponse schema."""
    
    def test_complete_response_with_all_fields(self):
        """Test CompleteOnboardingResponse with all fields."""
        response = CompleteOnboardingResponse(
            success=True,
            message="Onboarding completed successfully!",
            onboarding_status="completed",
            next_steps="Access your personalized content"
        )
        
        assert response.success is True
        assert response.onboarding_status == "completed"
        assert response.next_steps is not None
    
    def test_complete_response_without_next_steps(self):
        """Test CompleteOnboardingResponse without optional field."""
        response = CompleteOnboardingResponse(
            success=True,
            message="Completed",
            onboarding_status="completed"
        )
        
        assert response.next_steps is None