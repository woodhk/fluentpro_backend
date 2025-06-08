"""
Mock repository implementations for testing.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
from domains.onboarding.repositories.interfaces import IIndustryRepository, IPartnerRepository
from domains.authentication.models.user import User, UserProfile, OnboardingStatus
from domains.authentication.models.role import Role, RoleMatch, HierarchyLevel
# from infrastructure.persistence.event_store import IEventStore
# from domains.shared.events.base_event import DomainEvent


class MockUserRepository(IUserRepository):
    """Mock implementation of IUserRepository for testing."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.profiles: Dict[str, UserProfile] = {}
    
    async def find_by_id(self, id: str) -> Optional[User]:
        return self.users.get(id)
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[User]:
        users = list(self.users.values())
        if not filters:
            return users
        
        # Simple filter implementation
        filtered_users = []
        for user in users:
            match = True
            for key, value in filters.items():
                if not hasattr(user, key) or getattr(user, key) != value:
                    match = False
                    break
            if match:
                filtered_users.append(user)
        return filtered_users
    
    async def save(self, entity: User) -> User:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        self.users[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self.users:
            del self.users[id]
            if id in self.profiles:
                del self.profiles[id]
            return True
        return False
    
    async def exists(self, id: str) -> bool:
        return id in self.users
    
    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def find_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        for user in self.users.values():
            if user.auth0_id == auth0_id:
                return user
        return None
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.profiles.get(user_id)
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        profile = self.profiles.get(user_id)
        if not profile:
            # Create a basic profile
            user = self.users.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            profile = UserProfile(
                user_id=user_id,
                email=user.email,
                full_name=user.full_name,
                auth0_id=user.auth0_id
            )
        
        # Update profile with new data
        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.profiles[user_id] = profile
        return profile
    
    async def get_full_profile_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        user = await self.find_by_auth0_id(auth0_id)
        if not user:
            return None
        
        profile = await self.get_profile(user.id)
        return {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'auth0_id': user.auth0_id,
            'profile': profile.__dict__ if profile else None
        }
    
    async def get_users_by_status(self, status: OnboardingStatus) -> List[User]:
        return [user for user in self.users.values() if user.onboarding_status == status]
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        results = []
        query_lower = query.lower()
        for user in self.users.values():
            if (query_lower in user.full_name.lower() or 
                query_lower in user.email.lower()):
                results.append(user)
                if len(results) >= limit:
                    break
        return results
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        total = len(self.users)
        by_status = {}
        for status in OnboardingStatus:
            by_status[status.value] = len([u for u in self.users.values() if u.onboarding_status == status])
        
        return {
            'total_users': total,
            'by_status': by_status,
            'recent_registrations': total,  # Simplified
            'completion_rate': (by_status.get('completed', 0) / max(total, 1)) * 100
        }
    
    async def bulk_update_status(self, user_ids: List[str], status: OnboardingStatus) -> int:
        updated = 0
        for user_id in user_ids:
            if user_id in self.users:
                self.users[user_id].onboarding_status = status
                updated += 1
        return updated


class MockRoleRepository(IRoleRepository):
    """Mock implementation of IRoleRepository for testing."""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
    
    async def find_by_id(self, id: str) -> Optional[Role]:
        return self.roles.get(id)
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Role]:
        roles = list(self.roles.values())
        if not filters:
            return roles
        
        # Simple filter implementation
        filtered_roles = []
        for role in roles:
            match = True
            for key, value in filters.items():
                if not hasattr(role, key) or getattr(role, key) != value:
                    match = False
                    break
            if match:
                filtered_roles.append(role)
        return filtered_roles
    
    async def save(self, entity: Role) -> Role:
        if not entity.id:
            entity.id = str(uuid.uuid4())
        self.roles[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self.roles:
            del self.roles[id]
            return True
        return False
    
    async def exists(self, id: str) -> bool:
        return id in self.roles
    
    async def find_by_name(self, name: str) -> Optional[Role]:
        for role in self.roles.values():
            if role.title == name:
                return role
        return None
    
    async def search_by_embedding(self, embedding: List[float], limit: int = 10) -> List[RoleMatch]:
        # Simplified mock implementation
        roles = list(self.roles.values())[:limit]
        matches = []
        for i, role in enumerate(roles):
            match = RoleMatch(
                role=role,
                score=0.9 - (i * 0.1),  # Decreasing score
                embedding=embedding
            )
            matches.append(match)
        return matches
    
    async def get_by_industry(self, industry_id: str) -> List[Role]:
        return [role for role in self.roles.values() if role.industry_id == industry_id]
    
    async def get_statistics(self) -> Dict[str, Any]:
        total = len(self.roles)
        by_industry = {}
        for role in self.roles.values():
            industry_id = role.industry_id or 'none'
            by_industry[industry_id] = by_industry.get(industry_id, 0) + 1
        
        return {
            'total_roles': total,
            'by_industry': by_industry,
            'active_roles': len([r for r in self.roles.values() if r.is_active])
        }
    
    async def search_by_text(self, query: str, industry_id: Optional[str] = None, limit: int = 10) -> List[Role]:
        results = []
        query_lower = query.lower()
        for role in self.roles.values():
            if (query_lower in role.title.lower() or 
                query_lower in (role.description or '').lower()):
                if industry_id is None or role.industry_id == industry_id:
                    results.append(role)
                    if len(results) >= limit:
                        break
        return results
    
    async def get_roles_needing_embedding(self, limit: int = 100) -> List[Role]:
        # Mock: return roles without embeddings
        return list(self.roles.values())[:limit]
    
    async def update_embedding(self, role_id: str, embedding: List[float]) -> bool:
        if role_id in self.roles:
            # Mock: just return True
            return True
        return False


class MockIndustryRepository(IIndustryRepository):
    """Mock implementation of IIndustryRepository for testing."""
    
    def __init__(self):
        self.industries: Dict[str, Dict[str, Any]] = {
            '1': {'id': '1', 'name': 'Technology', 'role_count': 50},
            '2': {'id': '2', 'name': 'Healthcare', 'role_count': 30},
            '3': {'id': '3', 'name': 'Finance', 'role_count': 40}
        }
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return self.industries.get(id)
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return list(self.industries.values())
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        if 'id' not in entity:
            entity['id'] = str(uuid.uuid4())
        self.industries[entity['id']] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self.industries:
            del self.industries[id]
            return True
        return False
    
    async def exists(self, id: str) -> bool:
        return id in self.industries
    
    async def get_by_name(self, industry_name: str) -> Optional[Dict[str, Any]]:
        for industry in self.industries.values():
            if industry['name'] == industry_name:
                return industry
        return None
    
    async def get_with_role_counts(self) -> List[Dict[str, Any]]:
        return list(self.industries.values())
    
    async def get_popular_industries(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_industries = sorted(
            self.industries.values(), 
            key=lambda x: x.get('role_count', 0), 
            reverse=True
        )
        return sorted_industries[:limit]
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        query_lower = query.lower()
        for industry in self.industries.values():
            if query_lower in industry['name'].lower():
                results.append(industry)
                if len(results) >= limit:
                    break
        return results
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_industries': len(self.industries),
            'total_roles': sum(i.get('role_count', 0) for i in self.industries.values())
        }


class MockPartnerRepository(IPartnerRepository):
    """Mock implementation of IPartnerRepository for testing."""
    
    def __init__(self):
        self.partners: Dict[str, Dict[str, Any]] = {
            '1': {'id': '1', 'name': 'Senior Management', 'is_active': True},
            '2': {'id': '2', 'name': 'Customers', 'is_active': True},
            '3': {'id': '3', 'name': 'Colleagues', 'is_active': True}
        }
        self.units: Dict[str, Dict[str, Any]] = {
            '1': {'id': '1', 'name': 'Meetings', 'is_active': True},
            '2': {'id': '2', 'name': 'Presentations', 'is_active': True},
            '3': {'id': '3', 'name': 'Phone Calls', 'is_active': True}
        }
        self.user_partners: Dict[str, List[Dict[str, Any]]] = {}
        self.user_units: Dict[str, List[Dict[str, Any]]] = {}
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return self.partners.get(id)
    
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return list(self.partners.values())
    
    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        if 'id' not in entity:
            entity['id'] = str(uuid.uuid4())
        self.partners[entity['id']] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self.partners:
            del self.partners[id]
            return True
        return False
    
    async def exists(self, id: str) -> bool:
        return id in self.partners
    
    async def get_partners(self) -> List[Dict[str, Any]]:
        return [p for p in self.partners.values() if p.get('is_active', True)]
    
    async def get_units(self) -> List[Dict[str, Any]]:
        return [u for u in self.units.values() if u.get('is_active', True)]
    
    async def get_user_partners(self, user_id: str) -> List[Dict[str, Any]]:
        return self.user_partners.get(user_id, [])
    
    async def get_user_units(self, user_id: str, partner_id: str) -> List[Dict[str, Any]]:
        user_units = self.user_units.get(user_id, [])
        return [u for u in user_units if u.get('communication_partner_id') == partner_id]
    
    async def save_partner_selections(
        self, 
        user_id: str, 
        partner_ids: List[str],
        custom_partners: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        selections = []
        
        # Save standard partners
        for partner_id in partner_ids:
            partner = self.partners.get(partner_id)
            if partner:
                selection = {
                    'communication_partner_id': partner_id,
                    'partner_name': partner['name'],
                    'is_custom': False
                }
                selections.append(selection)
        
        # Save custom partners
        if custom_partners:
            for custom_name in custom_partners:
                selection = {
                    'communication_partner_id': '',
                    'partner_name': custom_name,
                    'is_custom': True,
                    'custom_partner_name': custom_name
                }
                selections.append(selection)
        
        self.user_partners[user_id] = selections
        return selections
    
    async def save_unit_selections(
        self,
        user_id: str,
        partner_id: str,
        unit_ids: List[str],
        custom_units: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        selections = []
        
        # Save standard units
        for unit_id in unit_ids:
            unit = self.units.get(unit_id)
            if unit:
                selection = {
                    'unit_id': unit_id,
                    'unit_name': unit['name'],
                    'is_custom': False
                }
                selections.append(selection)
        
        # Save custom units
        if custom_units:
            for custom_name in custom_units:
                selection = {
                    'unit_id': None,
                    'unit_name': custom_name,
                    'is_custom': True,
                    'custom_unit_name': custom_name,
                    'custom_unit_description': f"Custom communication situation: {custom_name}"
                }
                selections.append(selection)
        
        if user_id not in self.user_units:
            self.user_units[user_id] = []
        
        # Clear existing units for this partner
        self.user_units[user_id] = [
            u for u in self.user_units[user_id] 
            if u.get('communication_partner_id') != partner_id
        ]
        
        # Add new selections
        for selection in selections:
            selection['communication_partner_id'] = partner_id
            self.user_units[user_id].append(selection)
        
        return selections
    
    async def get_user_communication_needs(self, user_id: str) -> Dict[str, Any]:
        partners = self.user_partners.get(user_id, [])
        units = self.user_units.get(user_id, [])
        
        return {
            'user_id': user_id,
            'partners': [p['partner_name'] for p in partners],
            'units': units,
            'summary': {
                'partner_count': len(partners),
                'unit_count': len(units)
            }
        }
    
    async def get_partner_statistics(self) -> Dict[str, Any]:
        return {
            'total_partners': len(self.partners),
            'active_partners': len([p for p in self.partners.values() if p.get('is_active', True)]),
            'user_selections': len(self.user_partners)
        }
    
    async def get_unit_statistics(self) -> Dict[str, Any]:
        return {
            'total_units': len(self.units),
            'active_units': len([u for u in self.units.values() if u.get('is_active', True)]),
            'user_selections': len(self.user_units)
        }