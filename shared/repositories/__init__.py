"""
Repository implementations for data access layer.
Implements repository pattern with clear interfaces.
"""

from .user_repository import UserRepository
from .role_repository import RoleRepository
from .industry_repository import IndustryRepository
from .communication_repository import CommunicationRepository

__all__ = [
    'UserRepository',
    'RoleRepository', 
    'IndustryRepository',
    'CommunicationRepository'
]