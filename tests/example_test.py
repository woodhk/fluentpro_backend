"""
Example test file demonstrating mock repository usage.
"""

import pytest
from datetime import datetime, date

from tests.mocks.repositories import MockUserRepository, MockRoleRepository
from domains.authentication.models.user import User, OnboardingStatus, Language
from domains.authentication.models.role import Role, HierarchyLevel


@pytest.mark.asyncio
async def test_mock_user_repository():
    """Test MockUserRepository functionality."""
    # Arrange
    repo = MockUserRepository()
    user = User(
        email="test@example.com",
        full_name="Test User",
        date_of_birth=date(1990, 1, 1),
        auth0_id="auth0_123",
        native_language=Language.ENGLISH
    )
    
    # Act
    saved_user = await repo.save(user)
    retrieved_user = await repo.find_by_id(saved_user.id)
    
    # Assert
    assert saved_user.id is not None
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.full_name == "Test User"


@pytest.mark.asyncio
async def test_mock_role_repository():
    """Test MockRoleRepository functionality."""
    # Arrange
    repo = MockRoleRepository()
    role = Role(
        title="Software Engineer",
        description="Develops software applications",
        industry_id="tech_001",
        hierarchy_level=HierarchyLevel.ASSOCIATE,
        is_active=True
    )
    
    # Act
    saved_role = await repo.save(role)
    retrieved_role = await repo.find_by_id(saved_role.id)
    
    # Assert
    assert saved_role.id is not None
    assert retrieved_role is not None
    assert retrieved_role.title == "Software Engineer"
    assert retrieved_role.hierarchy_level == HierarchyLevel.ASSOCIATE


@pytest.mark.asyncio
async def test_mock_repositories_integration():
    """Test multiple mock repositories working together."""
    # Arrange
    user_repo = MockUserRepository()
    role_repo = MockRoleRepository()
    
    # Create test data
    user = User(
        email="integration@example.com",
        full_name="Integration Test User",
        date_of_birth=date(1985, 5, 15),
        auth0_id="auth0_integration",
        native_language=Language.SPANISH
    )
    
    role = Role(
        title="Product Manager",
        description="Manages product development",
        industry_id="business_001",
        hierarchy_level=HierarchyLevel.SENIOR,
        is_active=True
    )
    
    # Act
    saved_user = await user_repo.save(user)
    saved_role = await role_repo.save(role)
    
    # Update user with role
    saved_user.selected_role_id = saved_role.id
    updated_user = await user_repo.save(saved_user)
    
    # Verify integration
    retrieved_user = await user_repo.find_by_id(updated_user.id)
    retrieved_role = await role_repo.find_by_id(saved_role.id)
    
    # Assert
    assert retrieved_user.selected_role_id == retrieved_role.id
    assert retrieved_role.title == "Product Manager"
    assert retrieved_user.native_language == Language.SPANISH


if __name__ == "__main__":
    # Run with: python -m pytest tests/example_test.py -v
    pass