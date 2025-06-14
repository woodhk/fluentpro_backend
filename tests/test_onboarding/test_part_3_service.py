"""Tests for Onboarding Part 3 Service - TDD Phase 3"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.core.exceptions import UserNotFoundError
from src.models.enums import OnboardingStatus

# This import will fail initially - expected in TDD
try:
    from src.services.onboarding.summary_service import OnboardingSummaryService
except ImportError:
    pass


@pytest.fixture
def mock_db():
    """Mock Supabase client."""
    return MagicMock()


@pytest.fixture
def mock_user_data():
    """Mock user data."""
    return {
        "id": str(uuid4()),
        "auth0_id": "auth0|test123",
        "email": "test@example.com",
        "full_name": "Test User",
        "native_language": "english",
        "industry_id": str(uuid4()),
        "selected_role_id": str(uuid4()),
        "custom_role_title": None,
        "custom_role_description": None,
        "onboarding_status": "personalisation",
        "is_active": True
    }


class TestOnboardingSummaryService:
    """Test cases for OnboardingSummaryService."""
    
    def test_service_creation_fails(self, mock_db):
        """Test that OnboardingSummaryService doesn't exist yet."""
        with pytest.raises(NameError):
            service = OnboardingSummaryService(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_onboarding_summary_success(self, mock_db, mock_user_data):
        """Test successful retrieval of onboarding summary."""
        # Mock repositories
        with patch('src.services.onboarding.summary_service.ProfileRepository') as MockProfileRepo:
            with patch('src.services.onboarding.summary_service.JobRolesRepository') as MockRolesRepo:
                with patch('src.services.onboarding.summary_service.CommunicationRepository') as MockCommRepo:
                    # Setup mocks
                    mock_profile_repo = AsyncMock()
                    mock_profile_repo.get_user_by_auth0_id.return_value = mock_user_data
                    MockProfileRepo.return_value = mock_profile_repo
                    
                    # Mock industry query
                    mock_industry_result = MagicMock()
                    mock_industry_result.data = [{
                        "id": mock_user_data["industry_id"],
                        "name": "Banking & Finance"
                    }]
                    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_industry_result
                    
                    # Mock role
                    mock_roles_repo = AsyncMock()
                    mock_roles_repo.get_by_id.return_value = {
                        "id": mock_user_data["selected_role_id"],
                        "title": "Financial Analyst",
                        "description": "Analyzes financial data",
                        "is_system_role": True
                    }
                    MockRolesRepo.return_value = mock_roles_repo
                    
                    # Mock communication data
                    mock_comm_repo = AsyncMock()
                    mock_comm_repo.get_user_selected_partners.return_value = []
                    MockCommRepo.return_value = mock_comm_repo
                    
                    # Create service and test
                    service = OnboardingSummaryService(mock_db)
                    result = await service.get_onboarding_summary("auth0|test123")
                    
                    assert result["native_language"] == "english"
                    assert result["native_language_display"] == "English"
                    assert result["industry_name"] == "Banking & Finance"
                    assert result["role"]["title"] == "Financial Analyst"
                    assert result["role"]["is_custom"] is False
    
    @pytest.mark.asyncio
    async def test_get_onboarding_summary_user_not_found(self, mock_db):
        """Test when user is not found."""
        with patch('src.services.onboarding.summary_service.ProfileRepository') as MockProfileRepo:
            mock_profile_repo = AsyncMock()
            mock_profile_repo.get_user_by_auth0_id.return_value = None
            MockProfileRepo.return_value = mock_profile_repo
            
            service = OnboardingSummaryService(mock_db)
            
            with pytest.raises(UserNotFoundError):
                await service.get_onboarding_summary("auth0|nonexistent")
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_success(self, mock_db, mock_user_data):
        """Test successful onboarding completion."""
        # Set all required fields
        mock_user_data["native_language"] = "english"
        mock_user_data["industry_id"] = str(uuid4())
        mock_user_data["selected_role_id"] = str(uuid4())
        
        with patch('src.services.onboarding.summary_service.ProfileRepository') as MockProfileRepo:
            mock_profile_repo = AsyncMock()
            mock_profile_repo.get_user_by_auth0_id.return_value = mock_user_data
            mock_profile_repo.update.return_value = {
                **mock_user_data,
                "onboarding_status": OnboardingStatus.COMPLETED.value
            }
            MockProfileRepo.return_value = mock_profile_repo
            
            service = OnboardingSummaryService(mock_db)
            result = await service.complete_onboarding("auth0|test123")
            
            assert result["success"] is True
            assert result["onboarding_status"] == OnboardingStatus.COMPLETED.value
            assert "next_steps" in result
            
            # Verify update was called
            mock_profile_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_incomplete_fields(self, mock_db):
        """Test completion when required fields are missing."""
        incomplete_user = {
            "id": str(uuid4()),
            "auth0_id": "auth0|test123",
            "native_language": None,  # Missing
            "industry_id": None,      # Missing
            "selected_role_id": None, # Missing
        }
        
        with patch('src.services.onboarding.summary_service.ProfileRepository') as MockProfileRepo:
            mock_profile_repo = AsyncMock()
            mock_profile_repo.get_user_by_auth0_id.return_value = incomplete_user
            MockProfileRepo.return_value = mock_profile_repo
            
            service = OnboardingSummaryService(mock_db)
            
            with pytest.raises(ValueError) as exc_info:
                await service.complete_onboarding("auth0|test123")
            
            assert "Native language not selected" in str(exc_info.value)
            assert "Industry not selected" in str(exc_info.value)
            assert "Role not selected" in str(exc_info.value)
    
    def test_get_language_display_name(self, mock_db):
        """Test language display name mapping."""
        service = OnboardingSummaryService(mock_db)
        
        assert service._get_language_display_name("english") == "English"
        assert service._get_language_display_name("chinese_traditional") == "Traditional Chinese"
        assert service._get_language_display_name("chinese_simplified") == "Simplified Chinese"
        assert service._get_language_display_name(None) == "Not selected"
        assert service._get_language_display_name("unknown") == "Unknown"
    
    @pytest.mark.asyncio
    async def test_get_role_summary_with_custom_role(self, mock_db):
        """Test role summary for custom roles."""
        service = OnboardingSummaryService(mock_db)
        
        result = await service._get_role_summary(
            role_id=str(uuid4()),
            custom_title="Custom Developer",
            custom_description="Develops custom solutions",
            industry_name="Technology"
        )
        
        assert result["title"] == "Custom Developer"
        assert result["description"] == "Develops custom solutions"
        assert result["is_custom"] is True
        assert result["industry_name"] == "Technology"