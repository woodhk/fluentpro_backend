"""
Shared Value Objects

Domain value objects that represent business concepts with validation and behavior.
"""

from .email import Email
from .password import Password
from .user_id import UserId
from .phone_number import PhoneNumber

__all__ = [
    'Email',
    'Password', 
    'UserId',
    'PhoneNumber'
]