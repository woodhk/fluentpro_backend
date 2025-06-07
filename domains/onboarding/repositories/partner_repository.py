"""
Domain partner repository module.

This module only contains the interface definition.
For concrete implementations, see:
infrastructure/persistence/supabase/implementations/partner_repository_impl.py
"""

from .interfaces import IPartnerRepository

# Only export the interface from this domain module
__all__ = ['IPartnerRepository']