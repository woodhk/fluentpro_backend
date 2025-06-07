"""
Domain industry repository module.

This module only contains the interface definition.
For concrete implementations, see:
infrastructure/persistence/supabase/implementations/industry_repository_impl.py
"""

from .interfaces import IIndustryRepository

# Only export the interface from this domain module
__all__ = ['IIndustryRepository']