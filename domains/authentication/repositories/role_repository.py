"""
Domain role repository module.

This module only contains the interface definition.
For concrete implementations, see:
infrastructure/persistence/supabase/implementations/role_repository_impl.py
"""

from .interfaces import IRoleRepository

# Only export the interface from this domain module
__all__ = ['IRoleRepository']