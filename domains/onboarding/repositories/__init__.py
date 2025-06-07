"""Onboarding domain repositories."""

from .interfaces import IPartnerRepository, IIndustryRepository
from .partner_repository import PartnerRepository
from .industry_repository import IndustryRepository

__all__ = [
    'IPartnerRepository',
    'IIndustryRepository',
    'PartnerRepository',
    'IndustryRepository',
]