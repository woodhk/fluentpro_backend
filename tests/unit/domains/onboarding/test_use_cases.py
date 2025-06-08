import pytest
from datetime import datetime
from domains.onboarding.use_cases.start_onboarding_session import StartOnboardingSessionUseCase
from domains.onboarding.use_cases.select_user_industry import SelectUserIndustryUseCase
from domains.onboarding.dto.requests import StartOnboardingRequest, SelectIndustryRequest
from domains.onboarding.dto.responses import OnboardingSessionResponse, OnboardingStep, OnboardingSessionStatus
from domains.authentication.models.user import UserProfile, OnboardingStatus
from core.exceptions import SupabaseUserNotFoundError


class TestStartOnboardingSessionUseCase:
    @pytest.mark.asyncio
    async def test_start_new_onboarding_session(self, mock_user_repository):
        # Arrange
        user_id = "test-user-123"
        user_profile = UserProfile(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456",
            onboarding_status=OnboardingStatus.PENDING
        )
        
        # Add profile to repository
        mock_user_repository.profiles[user_id] = user_profile
        
        use_case = StartOnboardingSessionUseCase(
            user_repository=mock_user_repository
        )
        
        request = StartOnboardingRequest(user_id=user_id)
        
        # Act
        response = await use_case.execute(request)
        
        # Assert
        assert response.user_id == user_id
        assert response.status == OnboardingSessionStatus.ACTIVE
        assert response.current_step == OnboardingStep.LANGUAGE_SELECTION
        assert response.session_id.startswith(f"session-{user_id}")
        assert response.progress["language_selection"] is False
        assert response.progress["industry_selection"] is False
    
    @pytest.mark.asyncio
    async def test_resume_onboarding_session_with_progress(self, mock_user_repository):
        # Arrange
        user_id = "test-user-456"
        user_profile = UserProfile(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|456789",
            onboarding_status=OnboardingStatus.IN_PROGRESS,
            industry_id="tech-industry-id",
            native_language="en"
        )
        
        # Add profile to repository
        mock_user_repository.profiles[user_id] = user_profile
        
        use_case = StartOnboardingSessionUseCase(
            user_repository=mock_user_repository
        )
        
        request = StartOnboardingRequest(user_id=user_id)
        
        # Act
        response = await use_case.execute(request)
        
        # Assert
        assert response.user_id == user_id
        assert response.status == OnboardingSessionStatus.ACTIVE
        assert response.current_step == OnboardingStep.INDUSTRY_SELECTION
        assert response.progress["language_selection"] is True  # Has native language
        assert response.progress["industry_selection"] is True  # Has industry
        assert response.progress["role_selection"] is False
    
    @pytest.mark.asyncio
    async def test_user_not_found_error(self, mock_user_repository):
        # Arrange
        user_id = "non-existent-user"
        use_case = StartOnboardingSessionUseCase(
            user_repository=mock_user_repository
        )
        
        request = StartOnboardingRequest(user_id=user_id)
        
        # Act & Assert
        with pytest.raises(SupabaseUserNotFoundError):
            await use_case.execute(request)


class TestSelectUserIndustryUseCase:
    @pytest.mark.asyncio
    async def test_select_industry_successfully(self, mock_user_repository, mock_industry_repository):
        # Arrange
        user_id = "test-user-789"
        industry_id = "1"  # Technology industry
        
        # Create user profile
        user_profile = UserProfile(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|789012",
            onboarding_status=OnboardingStatus.PENDING
        )
        mock_user_repository.profiles[user_id] = user_profile
        
        # Add user to repository
        from domains.authentication.models.user import User
        user = User(
            id=user_id,
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|789012"
        )
        await mock_user_repository.save(user)
        
        use_case = SelectUserIndustryUseCase(
            user_repository=mock_user_repository,
            industry_repository=mock_industry_repository
        )
        
        request = SelectIndustryRequest(
            user_id=user_id,
            industry_id=industry_id
        )
        
        # Act
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is True
        assert response.industry_id == industry_id
        assert response.industry_name == "Technology"
        assert response.role_count == 50
        
        # Verify user profile was updated
        updated_profile = await mock_user_repository.get_profile(user_id)
        assert updated_profile.industry_id == industry_id
    
    @pytest.mark.asyncio
    async def test_invalid_industry_id(self, mock_user_repository, mock_industry_repository):
        # Arrange
        user_id = "test-user-999"
        invalid_industry_id = "invalid-industry"
        
        # Create user
        from domains.authentication.models.user import User
        user = User(
            id=user_id,
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|999999"
        )
        await mock_user_repository.save(user)
        
        use_case = SelectUserIndustryUseCase(
            user_repository=mock_user_repository,
            industry_repository=mock_industry_repository
        )
        
        request = SelectIndustryRequest(
            user_id=user_id,
            industry_id=invalid_industry_id
        )
        
        # Act
        response = await use_case.execute(request)
        
        # Assert
        assert response.success is False
        assert response.error == "Industry not found"
        assert response.industry_id is None
        assert response.industry_name is None