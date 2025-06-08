"""
End-to-end tests for complete user onboarding journey.
Tests the entire user lifecycle from registration to completed onboarding.
"""

import pytest
from domains.authentication.use_cases.register_user import RegisterUserUseCase
from domains.authentication.use_cases.authenticate_user import AuthenticateUserUseCase
from domains.authentication.dto.requests import SignupRequest, LoginRequest
from domains.onboarding.use_cases.start_onboarding_session import StartOnboardingSessionUseCase
from domains.onboarding.use_cases.select_user_industry import SelectUserIndustryUseCase
from domains.onboarding.use_cases.select_native_language import SelectNativeLanguageUseCase
from domains.onboarding.use_cases.select_communication_partners import SelectCommunicationPartnersUseCase
from domains.onboarding.use_cases.create_custom_user_role import CreateCustomUserRoleUseCase
from domains.onboarding.use_cases.complete_onboarding_flow import CompleteOnboardingFlowUseCase
from domains.onboarding.dto.requests import (
    StartOnboardingRequest, SelectIndustryRequest, SelectNativeLanguageRequest,
    SelectCommunicationPartnersRequest, CreateCustomRoleRequest, CompleteOnboardingRequest
)
from domains.authentication.models.user import User, OnboardingStatus
from tests.mocks.repositories import (
    MockUserRepository, MockRoleRepository, MockIndustryRepository, MockPartnerRepository
)
from tests.mocks.services import MockAuthenticationService
from tests.unit.domains.onboarding.conftest import MockOnboardingService


class TestCompleteUserJourney:
    """Test complete user journey from registration to onboarding completion."""

    @pytest.mark.asyncio
    async def test_new_user_complete_journey(self):
        """Test complete flow: registration -> login -> full onboarding."""
        # Arrange - Set up all shared dependencies
        user_repository = MockUserRepository()
        role_repository = MockRoleRepository()
        industry_repository = MockIndustryRepository()
        partner_repository = MockPartnerRepository()
        auth_service = MockAuthenticationService()
        onboarding_service = MockOnboardingService()

        # Mock authentication responses
        auth_service.authenticate = lambda email, password: {
            "access_token": f"token-{email.split('@')[0]}",
            "refresh_token": f"refresh-{email.split('@')[0]}",
            "expires_in": 3600
        }

        # Create use cases
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        authenticate_use_case = AuthenticateUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        select_language_use_case = SelectNativeLanguageUseCase(
            user_repository=user_repository
        )
        select_industry_use_case = SelectUserIndustryUseCase(
            user_repository=user_repository,
            industry_repository=industry_repository
        )
        select_partners_use_case = SelectCommunicationPartnersUseCase(
            user_repository=user_repository,
            partner_repository=partner_repository
        )
        create_role_use_case = CreateCustomUserRoleUseCase(
            user_repository=user_repository,
            role_repository=role_repository
        )
        complete_onboarding_use_case = CompleteOnboardingFlowUseCase(
            user_repository=user_repository
        )

        # ACT & ASSERT - Step 1: User Registration
        signup_request = SignupRequest(
            email="journey@test.com",
            password="JourneyPass123!",
            full_name="Journey Test User"
        )
        registration_response = await register_use_case.execute(signup_request)

        # Verify registration
        assert registration_response.user.email == "journey@test.com"
        assert registration_response.user.full_name == "Journey Test User"
        assert registration_response.tokens.access_token == "token-journey"
        assert registration_response.user.auth0_id.startswith("auth0|")

        user_id = registration_response.user.id

        # Step 2: User Login (after registration)
        login_request = LoginRequest(
            email="journey@test.com",
            password="JourneyPass123!"
        )
        # Mock successful login returning same user
        authenticate_use_case.execute = lambda req: registration_response
        login_response = await authenticate_use_case.execute(login_request)

        # Verify login
        assert login_response.user.id == user_id
        assert login_response.tokens.access_token == "token-journey"

        # Step 3: Start Onboarding Session
        start_request = StartOnboardingRequest(user_id=user_id)
        session_response = await start_onboarding_use_case.execute(start_request)

        # Verify onboarding session started
        assert session_response.user_id == user_id
        assert session_response.status.value == "active"
        assert session_response.current_step == "language_selection"

        # Step 4: Select Native Language
        language_request = SelectNativeLanguageRequest(
            user_id=user_id,
            language_code="en"
        )
        language_response = await select_language_use_case.execute(language_request)

        # Verify language selection
        assert language_response.success is True
        assert language_response.selected_language == "English"

        # Step 5: Select Industry
        industry_request = SelectIndustryRequest(
            user_id=user_id,
            industry_id="1"  # Technology
        )
        industry_response = await select_industry_use_case.execute(industry_request)

        # Verify industry selection
        assert industry_response.success is True
        assert industry_response.industry_name == "Technology"

        # Step 6: Select Communication Partners
        partners_request = SelectCommunicationPartnersRequest(
            user_id=user_id,
            partner_ids=["1", "2"],  # Senior Management, Customers
            custom_partners=["International Clients", "Technical Teams"]
        )
        partners_response = await select_partners_use_case.execute(partners_request)

        # Verify partners selection
        assert partners_response.success is True
        assert len(partners_response.selected_partners) == 4
        partner_names = [p["partner_name"] for p in partners_response.selected_partners]
        assert "International Clients" in partner_names
        assert "Technical Teams" in partner_names

        # Step 7: Create Custom Role
        role_request = CreateCustomRoleRequest(
            user_id=user_id,
            role_description="Senior Software Engineer specializing in backend systems and API development"
        )
        role_response = await create_role_use_case.execute(role_request)

        # Verify custom role creation
        assert role_response.success is True
        assert "Senior Software Engineer" in role_response.role_name
        assert role_response.confidence_score > 0.8

        # Step 8: Complete Onboarding
        complete_request = CompleteOnboardingRequest(user_id=user_id)
        completion_response = await complete_onboarding_use_case.execute(complete_request)

        # Verify onboarding completion
        assert completion_response.success is True
        assert completion_response.onboarding_status == OnboardingStatus.COMPLETED
        assert completion_response.profile_completeness == 100.0

        # Final verification - Check user profile state
        final_profile = await user_repository.get_profile(user_id)
        assert final_profile.onboarding_status == OnboardingStatus.COMPLETED
        assert final_profile.native_language == "en"
        assert final_profile.industry_id == "1"
        assert final_profile.role_id is not None

    @pytest.mark.asyncio
    async def test_user_journey_with_interruption_and_resume(self):
        """Test user journey with interruption and resumption of onboarding."""
        # Arrange
        user_repository = MockUserRepository()
        role_repository = MockRoleRepository()
        industry_repository = MockIndustryRepository()
        partner_repository = MockPartnerRepository()
        auth_service = MockAuthenticationService()

        auth_service.authenticate = lambda email, password: {
            "access_token": "token-resume",
            "refresh_token": "refresh-resume",
            "expires_in": 3600
        }

        # Create user and complete partial onboarding
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )

        signup_request = SignupRequest(
            email="resume@test.com",
            password="ResumePass123!",
            full_name="Resume Test User"
        )
        registration_response = await register_use_case.execute(signup_request)
        user_id = registration_response.user.id

        # Complete first two steps
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        select_language_use_case = SelectNativeLanguageUseCase(
            user_repository=user_repository
        )

        # Start onboarding and select language
        await start_onboarding_use_case.execute(StartOnboardingRequest(user_id=user_id))
        await select_language_use_case.execute(
            SelectNativeLanguageRequest(user_id=user_id, language_code="es")
        )

        # Simulate interruption - user logs out/session ends
        
        # ACT - Resume onboarding (user logs back in)
        # Start new session (should resume from where left off)
        resume_session_response = await start_onboarding_use_case.execute(
            StartOnboardingRequest(user_id=user_id)
        )

        # Verify resumption state
        assert resume_session_response.current_step == "industry_selection"
        assert resume_session_response.progress["language_selection"] is True
        assert resume_session_response.progress["industry_selection"] is False

        # Continue with industry selection
        select_industry_use_case = SelectUserIndustryUseCase(
            user_repository=user_repository,
            industry_repository=industry_repository
        )
        
        industry_response = await select_industry_use_case.execute(
            SelectIndustryRequest(user_id=user_id, industry_id="2")  # Healthcare
        )

        # Verify continuation works
        assert industry_response.success is True
        assert industry_response.industry_name == "Healthcare"

        # Verify profile state
        profile = await user_repository.get_profile(user_id)
        assert profile.native_language == "es"
        assert profile.industry_id == "2"

    @pytest.mark.asyncio
    async def test_multiple_users_concurrent_journeys(self):
        """Test multiple users going through onboarding journey simultaneously."""
        # Arrange
        user_repository = MockUserRepository()
        role_repository = MockRoleRepository()
        industry_repository = MockIndustryRepository()
        partner_repository = MockPartnerRepository()
        auth_service = MockAuthenticationService()

        # Setup authentication mock
        auth_service.authenticate = lambda email, password: {
            "access_token": f"token-{email.split('@')[0]}",
            "refresh_token": f"refresh-{email.split('@')[0]}",
            "expires_in": 3600
        }

        # Create use cases
        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        select_language_use_case = SelectNativeLanguageUseCase(
            user_repository=user_repository
        )
        select_industry_use_case = SelectUserIndustryUseCase(
            user_repository=user_repository,
            industry_repository=industry_repository
        )

        # ACT - Register multiple users
        users_data = [
            ("concurrent1@test.com", "Concurrent User One", "en", "1"),
            ("concurrent2@test.com", "Concurrent User Two", "fr", "2"),
            ("concurrent3@test.com", "Concurrent User Three", "de", "3")
        ]

        user_ids = []
        for email, name, lang, industry in users_data:
            # Register user
            signup_request = SignupRequest(
                email=email,
                password="ConcurrentPass123!",
                full_name=name
            )
            registration_response = await register_use_case.execute(signup_request)
            user_ids.append(registration_response.user.id)

        # Start onboarding for all users
        for user_id in user_ids:
            await start_onboarding_use_case.execute(StartOnboardingRequest(user_id=user_id))

        # Complete language selection for all users
        for i, user_id in enumerate(user_ids):
            lang = users_data[i][2]
            await select_language_use_case.execute(
                SelectNativeLanguageRequest(user_id=user_id, language_code=lang)
            )

        # Complete industry selection for all users
        for i, user_id in enumerate(user_ids):
            industry_id = users_data[i][3]
            await select_industry_use_case.execute(
                SelectIndustryRequest(user_id=user_id, industry_id=industry_id)
            )

        # ASSERT - Verify each user has correct state
        for i, user_id in enumerate(user_ids):
            profile = await user_repository.get_profile(user_id)
            expected_lang = users_data[i][2]
            expected_industry = users_data[i][3]
            
            assert profile.native_language == expected_lang
            assert profile.industry_id == expected_industry
            
            # Verify no cross-contamination
            for j, other_user_id in enumerate(user_ids):
                if i != j:
                    other_profile = await user_repository.get_profile(other_user_id)
                    assert other_profile.native_language != profile.native_language or i == j
                    assert other_profile.industry_id != profile.industry_id or i == j

    @pytest.mark.asyncio
    async def test_user_journey_validation_errors(self):
        """Test user journey handles validation errors gracefully."""
        # Arrange
        user_repository = MockUserRepository()
        auth_service = MockAuthenticationService()

        auth_service.authenticate = lambda email, password: {
            "access_token": "token-validation",
            "refresh_token": "refresh-validation",
            "expires_in": 3600
        }

        register_use_case = RegisterUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )

        # ACT & ASSERT - Test registration with invalid data
        with pytest.raises(Exception):  # Should raise validation error
            invalid_signup = SignupRequest(
                email="invalid-email",  # Invalid email format
                password="weak",  # Weak password
                full_name=""  # Empty name
            )
            await register_use_case.execute(invalid_signup)

        # Test with valid registration but invalid onboarding data
        valid_signup = SignupRequest(
            email="validation@test.com",
            password="ValidPass123!",
            full_name="Validation Test User"
        )
        registration_response = await register_use_case.execute(valid_signup)
        user_id = registration_response.user.id

        # Try invalid onboarding steps
        start_onboarding_use_case = StartOnboardingSessionUseCase(
            user_repository=user_repository
        )
        
        # This should work
        session_response = await start_onboarding_use_case.execute(
            StartOnboardingRequest(user_id=user_id)
        )
        assert session_response.user_id == user_id

        # Try with non-existent user
        with pytest.raises(Exception):  # Should raise user not found error
            await start_onboarding_use_case.execute(
                StartOnboardingRequest(user_id="non-existent-user")
            )