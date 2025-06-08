"""
Integration tests for onboarding flow.
These tests verify the complete onboarding flow with mocked services.
"""

import pytest
from domains.onboarding.use_cases.start_onboarding_session import StartOnboardingSessionUseCase
from domains.onboarding.use_cases.select_user_industry import SelectUserIndustryUseCase
from domains.onboarding.use_cases.select_communication_partners import SelectCommunicationPartnersUseCase
from domains.onboarding.dto.requests import (
    StartOnboardingRequest, SelectIndustryRequest, 
    SelectCommunicationPartnersRequest
)
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from tests.mocks.repositories import (
    MockUserRepository, MockIndustryRepository, MockPartnerRepository
)
from tests.unit.domains.onboarding.conftest import MockOnboardingService


class TestOnboardingFlow:
    """Test complete onboarding flows with integrated components."""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(self):
        # Arrange - Create shared dependencies
        user_repository = MockUserRepository()
        industry_repository = MockIndustryRepository()
        partner_repository = MockPartnerRepository()
        onboarding_service = MockOnboardingService()
        
        # Create test user
        user = User(
            id="flow-test-user",
            email="flow@test.com",
            full_name="Flow Test User",
            auth0_id="auth0|flow123"
        )
        await user_repository.save(user)
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            auth0_id=user.auth0_id,
            onboarding_status=OnboardingStatus.PENDING
        )
        user_repository.profiles[user.id] = profile
        
        # Act - Start onboarding
        start_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        
        start_request = StartOnboardingRequest(user_id=user.id)
        session_response = await start_use_case.execute(start_request)
        
        # Assert session started
        assert session_response.user_id == user.id
        assert session_response.status.value == "active"
        assert session_response.progress["language_selection"] is False
        
        # Act - Select industry
        select_industry_use_case = SelectUserIndustryUseCase(
            user_repository=user_repository,
            industry_repository=industry_repository
        )
        
        industry_request = SelectIndustryRequest(
            user_id=user.id,
            industry_id="1"  # Technology
        )
        
        industry_response = await select_industry_use_case.execute(industry_request)
        
        # Assert industry selected
        assert industry_response.success is True
        assert industry_response.industry_name == "Technology"
        
        # Verify profile updated
        updated_profile = await user_repository.get_profile(user.id)
        assert updated_profile.industry_id == "1"
        
        # Act - Select communication partners
        select_partners_use_case = SelectCommunicationPartnersUseCase(
            user_repository=user_repository,
            partner_repository=partner_repository
        )
        
        partners_request = SelectCommunicationPartnersRequest(
            user_id=user.id,
            partner_ids=["1", "2"],  # Senior Management, Customers
            custom_partners=["Investors"]
        )
        
        partners_response = await select_partners_use_case.execute(partners_request)
        
        # Assert partners selected
        assert partners_response.success is True
        assert len(partners_response.selected_partners) == 3
        assert "Investors" in [p["partner_name"] for p in partners_response.selected_partners]
    
    @pytest.mark.asyncio
    async def test_resume_incomplete_onboarding(self):
        # Arrange - User with partially completed onboarding
        user_repository = MockUserRepository()
        
        user = User(
            id="resume-test-user",
            email="resume@test.com",
            full_name="Resume Test User",
            auth0_id="auth0|resume123"
        )
        await user_repository.save(user)
        
        # Profile with some progress
        profile = UserProfile(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            auth0_id=user.auth0_id,
            onboarding_status=OnboardingStatus.IN_PROGRESS,
            native_language="en",
            industry_id="2"  # Healthcare
        )
        user_repository.profiles[user.id] = profile
        
        # Act - Resume onboarding
        start_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        
        start_request = StartOnboardingRequest(user_id=user.id)
        session_response = await start_use_case.execute(start_request)
        
        # Assert - Session shows correct progress
        assert session_response.progress["language_selection"] is True  # Completed
        assert session_response.progress["industry_selection"] is True  # Completed
        assert session_response.progress["role_selection"] is False  # Not completed
    
    @pytest.mark.asyncio
    async def test_parallel_onboarding_sessions(self):
        """Test that multiple users can onboard simultaneously without interference."""
        # Arrange
        user_repository = MockUserRepository()
        industry_repository = MockIndustryRepository()
        
        # Create multiple users
        users = []
        for i in range(3):
            user = User(
                id=f"parallel-user-{i}",
                email=f"parallel{i}@test.com",
                full_name=f"Parallel User {i}",
                auth0_id=f"auth0|parallel{i}"
            )
            await user_repository.save(user)
            
            profile = UserProfile(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                auth0_id=user.auth0_id
            )
            user_repository.profiles[user.id] = profile
            users.append(user)
        
        # Act - Start sessions for all users
        start_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        
        sessions = []
        for user in users:
            request = StartOnboardingRequest(user_id=user.id)
            response = await start_use_case.execute(request)
            sessions.append(response)
        
        # Act - Each user selects different industry
        select_industry_use_case = SelectUserIndustryUseCase(
            user_repository=user_repository,
            industry_repository=industry_repository
        )
        
        industry_ids = ["1", "2", "3"]  # Tech, Healthcare, Finance
        for i, (user, industry_id) in enumerate(zip(users, industry_ids)):
            request = SelectIndustryRequest(
                user_id=user.id,
                industry_id=industry_id
            )
            await select_industry_use_case.execute(request)
        
        # Assert - Each user has their own progress
        for i, user in enumerate(users):
            profile = await user_repository.get_profile(user.id)
            assert profile.industry_id == industry_ids[i]
            
            # Verify no cross-contamination
            for j, other_user in enumerate(users):
                if i != j:
                    other_profile = await user_repository.get_profile(other_user.id)
                    assert other_profile.industry_id != profile.industry_id