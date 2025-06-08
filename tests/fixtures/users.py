"""
User factory and fixtures for testing.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.authentication.models.role import Role, HierarchyLevel


class UserFactory:
    """Factory for creating test users with various configurations."""
    
    @staticmethod
    def create_user(
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        auth0_id: Optional[str] = None,
        is_active: bool = True,
        onboarding_status: OnboardingStatus = OnboardingStatus.PENDING,
        **kwargs
    ) -> User:
        """Create a basic user with default values."""
        return User(
            id=kwargs.get('id', str(uuid.uuid4())),
            email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
            full_name=full_name or f"Test User {uuid.uuid4().hex[:8]}",
            auth0_id=auth0_id or f"auth0|{uuid.uuid4()}",
            is_active=is_active,
            onboarding_status=onboarding_status,
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_pending_user() -> User:
        """Create a user with pending onboarding status."""
        return UserFactory.create_user(
            onboarding_status=OnboardingStatus.PENDING,
            full_name="Pending User"
        )
    
    @staticmethod
    def create_in_progress_user() -> User:
        """Create a user with in-progress onboarding status."""
        return UserFactory.create_user(
            onboarding_status=OnboardingStatus.IN_PROGRESS,
            full_name="In Progress User"
        )
    
    @staticmethod
    def create_completed_user() -> User:
        """Create a user with completed onboarding status."""
        return UserFactory.create_user(
            onboarding_status=OnboardingStatus.COMPLETED,
            full_name="Completed User"
        )
    
    @staticmethod
    def create_executive_user() -> User:
        """Create a user representing an executive."""
        return UserFactory.create_user(
            email="executive@company.com",
            full_name="Executive User",
            onboarding_status=OnboardingStatus.COMPLETED
        )
    
    @staticmethod
    def create_manager_user() -> User:
        """Create a user representing a manager."""
        return UserFactory.create_user(
            email="manager@company.com",
            full_name="Manager User",
            onboarding_status=OnboardingStatus.COMPLETED
        )
    
    @staticmethod
    def create_employee_user() -> User:
        """Create a user representing an employee."""
        return UserFactory.create_user(
            email="employee@company.com",
            full_name="Employee User",
            onboarding_status=OnboardingStatus.IN_PROGRESS
        )
    
    @staticmethod
    def create_inactive_user() -> User:
        """Create an inactive user."""
        return UserFactory.create_user(
            is_active=False,
            full_name="Inactive User"
        )


class UserProfileFactory:
    """Factory for creating test user profiles."""
    
    @staticmethod
    def create_profile(
        user_id: str,
        email: str,
        full_name: str,
        auth0_id: str,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferred_language: str = "en",
        **kwargs
    ) -> UserProfile:
        """Create a user profile with default values."""
        return UserProfile(
            user_id=user_id,
            email=email,
            full_name=full_name,
            auth0_id=auth0_id,
            bio=bio or f"Bio for {full_name}",
            avatar_url=avatar_url or f"https://example.com/avatar/{user_id}.jpg",
            preferred_language=preferred_language,
            **kwargs
        )
    
    @staticmethod
    def create_complete_profile(user: User) -> UserProfile:
        """Create a complete profile for a user."""
        return UserProfileFactory.create_profile(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            auth0_id=user.auth0_id,
            bio=f"Experienced professional in their field. {user.full_name} is passionate about continuous learning and growth.",
            timezone="UTC",
            locale="en_US",
            phone_number="+1-555-0123",
            company="Example Corp",
            department="Engineering",
            job_title="Senior Developer"
        )


class RoleFactory:
    """Factory for creating test roles."""
    
    @staticmethod
    def create_role(
        title: Optional[str] = None,
        description: Optional[str] = None,
        industry_id: Optional[str] = None,
        hierarchy_level: HierarchyLevel = HierarchyLevel.INDIVIDUAL_CONTRIBUTOR,
        is_active: bool = True,
        **kwargs
    ) -> Role:
        """Create a basic role with default values."""
        role_id = str(uuid.uuid4())
        return Role(
            id=kwargs.get('id', role_id),
            title=title or f"Test Role {uuid.uuid4().hex[:8]}",
            description=description or f"Description for test role {role_id}",
            industry_id=industry_id or "tech",
            hierarchy_level=hierarchy_level,
            is_active=is_active,
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_executive_role() -> Role:
        """Create an executive-level role."""
        return RoleFactory.create_role(
            title="Chief Executive Officer",
            description="Responsible for overall company strategy and operations",
            hierarchy_level=HierarchyLevel.EXECUTIVE,
            industry_id="general"
        )
    
    @staticmethod
    def create_manager_role() -> Role:
        """Create a manager-level role."""
        return RoleFactory.create_role(
            title="Engineering Manager",
            description="Manages engineering teams and technical projects",
            hierarchy_level=HierarchyLevel.MANAGER,
            industry_id="tech"
        )
    
    @staticmethod
    def create_employee_role() -> Role:
        """Create an individual contributor role."""
        return RoleFactory.create_role(
            title="Software Engineer",
            description="Develops and maintains software applications",
            hierarchy_level=HierarchyLevel.INDIVIDUAL_CONTRIBUTOR,
            industry_id="tech"
        )


def create_user_with_role_scenarios() -> List[Dict[str, Any]]:
    """Create common user-role combination scenarios for testing."""
    scenarios = []
    
    # Executive with executive role
    exec_user = UserFactory.create_executive_user()
    exec_role = RoleFactory.create_executive_role()
    scenarios.append({
        'name': 'executive_scenario',
        'user': exec_user,
        'role': exec_role,
        'profile': UserProfileFactory.create_complete_profile(exec_user)
    })
    
    # Manager with manager role
    mgr_user = UserFactory.create_manager_user()
    mgr_role = RoleFactory.create_manager_role()
    scenarios.append({
        'name': 'manager_scenario',
        'user': mgr_user,
        'role': mgr_role,
        'profile': UserProfileFactory.create_complete_profile(mgr_user)
    })
    
    # Employee with employee role
    emp_user = UserFactory.create_employee_user()
    emp_role = RoleFactory.create_employee_role()
    scenarios.append({
        'name': 'employee_scenario',
        'user': emp_user,
        'role': emp_role,
        'profile': UserProfileFactory.create_complete_profile(emp_user)
    })
    
    return scenarios


def create_batch_users(count: int = 10) -> List[User]:
    """Create a batch of users for bulk testing."""
    users = []
    statuses = list(OnboardingStatus)
    
    for i in range(count):
        status = statuses[i % len(statuses)]
        user = UserFactory.create_user(
            email=f"batch-user-{i}@example.com",
            full_name=f"Batch User {i}",
            onboarding_status=status
        )
        users.append(user)
    
    return users