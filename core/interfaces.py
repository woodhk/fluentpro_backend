"""
Core interfaces for repositories and services.
Defines contracts for data access and external service integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from authentication.models.user import User, UserProfile
from authentication.models.role import Role, RoleMatch, JobDescription
from authentication.models.auth import TokenInfo, AuthSession
from onboarding.models.communication import (
    CommunicationPartner, 
    Unit, 
    UserCommunicationPartnerSelection,
    UserUnitSelection,
    UserCommunicationNeed
)


# =============================================================================
# Repository Interfaces
# =============================================================================

class UserRepositoryInterface(ABC):
    """Interface for user data access operations."""
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    def get_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        """Get user by Auth0 ID."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass
    
    @abstractmethod
    def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    def update(self, user_id: str, data: Dict[str, Any]) -> User:
        """Update user data."""
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete user."""
        pass
    
    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        pass
    
    @abstractmethod
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Update user profile."""
        pass
    
    @abstractmethod
    def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with joined data."""
        pass


class RoleRepositoryInterface(ABC):
    """Interface for role data access operations."""
    
    @abstractmethod
    def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        pass
    
    @abstractmethod
    def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        """Search roles by embedding similarity."""
        pass
    
    @abstractmethod
    def create(self, role_data: Dict[str, Any]) -> Role:
        """Create a new role."""
        pass
    
    @abstractmethod
    def update(self, role_id: str, data: Dict[str, Any]) -> Role:
        """Update role data."""
        pass
    
    @abstractmethod
    def get_by_industry(self, industry_id: str) -> List[Role]:
        """Get roles by industry."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get role usage statistics."""
        pass


class IndustryRepositoryInterface(ABC):
    """Interface for industry data access operations."""
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active industries."""
        pass
    
    @abstractmethod
    def get_by_id(self, industry_id: str) -> Optional[Dict[str, Any]]:
        """Get industry by ID."""
        pass
    
    @abstractmethod
    def create(self, industry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new industry."""
        pass


class CommunicationRepositoryInterface(ABC):
    """Interface for communication data access operations."""
    
    @abstractmethod
    def get_partners(self) -> List[CommunicationPartner]:
        """Get all active communication partners."""
        pass
    
    @abstractmethod
    def get_units(self) -> List[Unit]:
        """Get all active communication units."""
        pass
    
    @abstractmethod
    def get_user_partners(self, user_id: str) -> List[UserCommunicationPartnerSelection]:
        """Get user's selected partners."""
        pass
    
    @abstractmethod
    def get_user_units(self, user_id: str, partner_id: str) -> List[UserUnitSelection]:
        """Get user's selected units for a partner."""
        pass
    
    @abstractmethod
    def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[UserCommunicationPartnerSelection]:
        """Save user's partner selections."""
        pass
    
    @abstractmethod
    def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[UserUnitSelection]:
        """Save user's unit selections for a partner."""
        pass
    
    @abstractmethod
    def get_user_communication_needs(self, user_id: str) -> UserCommunicationNeed:
        """Get complete communication needs for a user."""
        pass


# =============================================================================
# Service Interfaces
# =============================================================================

class AuthServiceInterface(ABC):
    """Interface for authentication service operations."""
    
    @abstractmethod
    def authenticate(self, email: str, password: str) -> TokenInfo:
        """Authenticate user with email/password."""
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> TokenInfo:
        """Refresh access token."""
        pass
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user in Auth0."""
        pass
    
    @abstractmethod
    def logout_user(self, refresh_token: str) -> bool:
        """Logout user and revoke tokens."""
        pass
    
    @abstractmethod
    def validate_token(self, access_token: str) -> Dict[str, Any]:
        """Validate access token and return user info."""
        pass


class EmbeddingServiceInterface(ABC):
    """Interface for embedding generation services."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    def generate_role_embedding(self, role_data: Dict[str, Any]) -> List[float]:
        """Generate embedding for role data."""
        pass
    
    @abstractmethod
    def generate_job_embedding(self, job_description: JobDescription) -> List[float]:
        """Generate embedding for job description."""
        pass


class SearchServiceInterface(ABC):
    """Interface for search service operations."""
    
    @abstractmethod
    def search_roles(
        self, 
        embedding: List[float], 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search roles using vector similarity."""
        pass
    
    @abstractmethod
    def index_role(self, role_data: Dict[str, Any]) -> bool:
        """Index a role for search."""
        pass
    
    @abstractmethod
    def update_role_index(self, role_id: str, role_data: Dict[str, Any]) -> bool:
        """Update role in search index."""
        pass
    
    @abstractmethod
    def delete_role_from_index(self, role_id: str) -> bool:
        """Remove role from search index."""
        pass


class LLMServiceInterface(ABC):
    """Interface for Large Language Model operations."""
    
    @abstractmethod
    def rewrite_role_description(
        self, 
        original_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Rewrite role description for clarity and engagement."""
        pass
    
    @abstractmethod
    def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze job description and extract key information."""
        pass
    
    @abstractmethod
    def generate_role_suggestions(
        self, 
        job_title: str, 
        job_description: str,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate role suggestions based on job input."""
        pass


class DatabaseServiceInterface(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute raw database query."""
        pass
    
    @abstractmethod
    def get_table(self, table_name: str):
        """Get table reference for operations."""
        pass
    
    @abstractmethod
    def transaction(self):
        """Start database transaction context."""
        pass


# =============================================================================
# Cache Service Interface
# =============================================================================

class CacheServiceInterface(ABC):
    """Interface for cache service implementations."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


# =============================================================================
# Unit of Work Interface
# =============================================================================

class UnitOfWorkInterface(ABC):
    """Interface for Unit of Work pattern."""
    
    @abstractmethod
    def __enter__(self):
        """Enter context manager."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass
    
    @abstractmethod
    def commit(self):
        """Commit all pending changes."""
        pass
    
    @abstractmethod
    def rollback(self):
        """Rollback all pending changes."""
        pass
    
    @property
    @abstractmethod
    def users(self) -> UserRepositoryInterface:
        """Get user repository."""
        pass
    
    @property
    @abstractmethod
    def roles(self) -> RoleRepositoryInterface:
        """Get role repository."""
        pass
    
    @property
    @abstractmethod
    def industries(self) -> IndustryRepositoryInterface:
        """Get industry repository."""
        pass
    
    @property
    @abstractmethod
    def communication(self) -> CommunicationRepositoryInterface:
        """Get communication repository."""
        pass