import pytest
from datetime import datetime
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.shared.value_objects.email import Email
from domains.shared.value_objects.password import Password


class TestUserModel:
    def test_create_user_with_valid_data(self):
        # Arrange & Act
        user = User(
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        
        # Assert
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.auth0_id == "auth0|123456"
        assert user.is_active is True
        assert user.onboarding_status == OnboardingStatus.PENDING
    
    def test_user_id_generation(self):
        # Arrange & Act
        user1 = User(
            email="user1@example.com",
            full_name="User One",
            auth0_id="auth0|111111"
        )
        user2 = User(
            email="user2@example.com",
            full_name="User Two",
            auth0_id="auth0|222222"
        )
        
        # Assert
        assert user1.id is not None
        assert user2.id is not None
        assert user1.id != user2.id
    
    def test_user_timestamps(self):
        # Arrange
        before_creation = datetime.utcnow()
        
        # Act
        user = User(
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        after_creation = datetime.utcnow()
        
        # Assert
        assert user.created_at is not None
        assert user.updated_at is not None
        assert before_creation <= user.created_at <= after_creation
        assert user.created_at == user.updated_at
    
    def test_user_onboarding_status_transition(self):
        # Arrange
        user = User(
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        
        # Act & Assert
        assert user.onboarding_status == OnboardingStatus.PENDING
        
        user.onboarding_status = OnboardingStatus.IN_PROGRESS
        assert user.onboarding_status == OnboardingStatus.IN_PROGRESS
        
        user.onboarding_status = OnboardingStatus.COMPLETED
        assert user.onboarding_status == OnboardingStatus.COMPLETED
    
    def test_user_equality(self):
        # Arrange
        user1 = User(
            id="same-id",
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        user2 = User(
            id="same-id",
            email="different@example.com",
            full_name="Different User",
            auth0_id="auth0|654321"
        )
        user3 = User(
            id="different-id",
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        
        # Assert
        assert user1 == user2  # Same ID means same user
        assert user1 != user3  # Different ID means different user


class TestUserProfile:
    def test_create_user_profile(self):
        # Arrange & Act
        profile = UserProfile(
            user_id="user-123",
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        
        # Assert
        assert profile.user_id == "user-123"
        assert profile.email == "test@example.com"
        assert profile.full_name == "Test User"
        assert profile.auth0_id == "auth0|123456"
    
    def test_profile_with_additional_fields(self):
        # Arrange & Act
        profile = UserProfile(
            user_id="user-123",
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456",
            bio="A passionate language learner",
            avatar_url="https://example.com/avatar.jpg",
            preferred_language="en"
        )
        
        # Assert
        assert profile.bio == "A passionate language learner"
        assert profile.avatar_url == "https://example.com/avatar.jpg"
        assert profile.preferred_language == "en"
    
    def test_profile_update(self):
        # Arrange
        profile = UserProfile(
            user_id="user-123",
            email="test@example.com",
            full_name="Test User",
            auth0_id="auth0|123456"
        )
        
        # Act
        profile.full_name = "Updated Name"
        profile.bio = "New bio"
        
        # Assert
        assert profile.full_name == "Updated Name"
        assert profile.bio == "New bio"