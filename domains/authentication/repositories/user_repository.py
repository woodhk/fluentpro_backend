"""
Domain user repository module.

This module only contains the interface definition.
For concrete implementations, see:
infrastructure/persistence/supabase/implementations/user_repository_impl.py
"""

from .interfaces import IUserRepository

# Only export the interface from this domain module
__all__ = ['IUserRepository']