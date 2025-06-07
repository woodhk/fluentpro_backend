"""
Supabase repository implementations.

This module contains concrete implementations of domain repository interfaces
using Supabase as the persistence layer.
"""

from .user_repository_impl import UserRepositoryImpl
from .role_repository_impl import RoleRepositoryImpl
from .partner_repository_impl import PartnerRepositoryImpl
from .industry_repository_impl import IndustryRepositoryImpl

__all__ = [
    'UserRepositoryImpl',
    'RoleRepositoryImpl',
    'PartnerRepositoryImpl',
    'IndustryRepositoryImpl',
]