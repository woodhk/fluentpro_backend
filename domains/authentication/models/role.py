"""
Role and industry domain models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from domains.shared.models.base_entity import BaseEntity


class HierarchyLevel(Enum):
    """Enumeration of role hierarchy levels."""
    ASSOCIATE = "associate"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class RoleSource(Enum):
    """Enumeration of how a role was obtained."""
    SELECTED = "selected"  # User selected from existing roles
    CREATED = "created"    # User created a new role


class Industry(BaseEntity):
    """
    Industry domain model.
    """
    
    def __init__(self, name: str, id: Optional[str] = None, 
                 description: Optional[str] = None, sort_order: int = 0,
                 is_active: bool = True, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id  # Will be set by repository
        self.name = name
        self.description = description
        self.sort_order = sort_order
        self.is_active = is_active
        
        # Override timestamps if provided (for reconstruction from DB)
        if created_at:
            self.created_at = created_at
        if updated_at:
            self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert industry to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'Industry':
        """Create Industry instance from Supabase data."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(
            name=data['name'],
            id=data['id'],
            description=data.get('description'),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True),
            created_at=created_at,
            updated_at=updated_at
        )


class Role(BaseEntity):
    """
    Role domain model representing job roles/positions.
    """
    
    def __init__(self, title: str, description: str, industry_id: str,
                 id: Optional[str] = None, industry_name: Optional[str] = None,
                 hierarchy_level: HierarchyLevel = HierarchyLevel.ASSOCIATE,
                 search_keywords: Optional[List[str]] = None,
                 is_active: bool = True, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id  # Will be set by repository
        self.title = title
        self.description = description
        self.industry_id = industry_id
        self.industry_name = industry_name
        self.hierarchy_level = hierarchy_level
        self.search_keywords = search_keywords or []
        self.is_active = is_active
        
        # Override timestamps if provided (for reconstruction from DB)
        if created_at:
            self.created_at = created_at
        if updated_at:
            self.updated_at = updated_at
    
    @property
    def keywords_as_string(self) -> str:
        """Get search keywords as a space-separated string."""
        return ' '.join(self.search_keywords) if self.search_keywords else ''
    
    def add_keyword(self, keyword: str) -> None:
        """Add a search keyword if not already present."""
        if keyword and keyword.lower() not in [k.lower() for k in self.search_keywords]:
            self.search_keywords.append(keyword.lower())
    
    def remove_keyword(self, keyword: str) -> None:
        """Remove a search keyword."""
        self.search_keywords = [k for k in self.search_keywords if k.lower() != keyword.lower()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'industry_id': self.industry_id,
            'industry_name': self.industry_name,
            'hierarchy_level': self.hierarchy_level.value,
            'search_keywords': self.search_keywords,
            'keywords_string': self.keywords_as_string,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_search_document(self) -> Dict[str, Any]:
        """Convert role to Azure Search document format."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'industry_id': self.industry_id,
            'industry_name': self.industry_name or '',
            'hierarchy_level': self.hierarchy_level.value,
            'search_keywords': self.keywords_as_string,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_supabase_data(cls, data: Dict[str, Any]) -> 'Role':
        """Create Role instance from Supabase data."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        hierarchy_level = HierarchyLevel.ASSOCIATE
        if data.get('hierarchy_level'):
            try:
                hierarchy_level = HierarchyLevel(data['hierarchy_level'])
            except ValueError:
                pass  # Keep default if invalid value
        
        search_keywords = data.get('search_keywords', [])
        if isinstance(search_keywords, str):
            # Handle case where keywords are stored as comma-separated string
            search_keywords = [k.strip() for k in search_keywords.split(',') if k.strip()]
        elif not isinstance(search_keywords, list):
            search_keywords = []
        
        return cls(
            title=data['title'],
            description=data['description'],
            industry_id=data['industry_id'],
            id=data['id'],
            industry_name=data.get('industry_name'),
            hierarchy_level=hierarchy_level,
            search_keywords=search_keywords,
            is_active=data.get('is_active', True),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class UserRoleSelection:
    """
    Represents a user's role selection with metadata.
    """
    user_id: str
    role_id: str
    role_source: RoleSource
    selected_at: datetime
    role_details: Optional[Dict[str, Any]] = None
    
    @property
    def is_custom_role(self) -> bool:
        """Check if this is a custom (created) role."""
        return self.role_source == RoleSource.CREATED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role selection to dictionary."""
        return {
            'user_id': self.user_id,
            'role_id': self.role_id,
            'role_source': self.role_source.value,
            'selected_at': self.selected_at.isoformat(),
            'is_custom_role': self.is_custom_role,
            'role_details': self.role_details or {}
        }


@dataclass
class RoleMatch:
    """
    Represents a role match from search results.
    """
    role: Role
    relevance_score: float
    match_reasons: List[str] = field(default_factory=list)
    
    @property
    def is_good_match(self) -> bool:
        """Check if this is considered a good match (score > 0.7)."""
        return self.relevance_score > 0.7
    
    @property
    def is_excellent_match(self) -> bool:
        """Check if this is considered an excellent match (score > 0.9)."""
        return self.relevance_score > 0.9
    
    def add_match_reason(self, reason: str) -> None:
        """Add a reason why this role matched."""
        if reason not in self.match_reasons:
            self.match_reasons.append(reason)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role match to dictionary for API responses."""
        result = self.role.to_dict()
        result.update({
            'relevance_score': self.relevance_score,
            'match_reasons': self.match_reasons,
            'is_good_match': self.is_good_match,
            'is_excellent_match': self.is_excellent_match
        })
        return result


@dataclass
class JobDescription:
    """
    Represents a job description for role matching.
    """
    title: str
    description: str
    industry: Optional[str] = None
    hierarchy_level: HierarchyLevel = HierarchyLevel.ASSOCIATE
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    
    @property
    def all_skills(self) -> List[str]:
        """Get all skills (required + preferred)."""
        return self.required_skills + self.preferred_skills
    
    @property
    def search_text(self) -> str:
        """Get searchable text representation."""
        parts = [self.title, self.description]
        if self.industry:
            parts.append(f"Industry: {self.industry}")
        if self.all_skills:
            parts.append(f"Skills: {', '.join(self.all_skills)}")
        return ' '.join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job description to dictionary."""
        return {
            'title': self.title,
            'description': self.description,
            'industry': self.industry,
            'hierarchy_level': self.hierarchy_level.value,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'all_skills': self.all_skills,
            'search_text': self.search_text
        }