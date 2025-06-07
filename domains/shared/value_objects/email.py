from core.patterns.value_object import ValueObject
from core.utils.validation_utils import is_valid_email
from dataclasses import dataclass

@dataclass(frozen=True)
class Email(ValueObject):
    value: str
    
    def _validate(self):
        if not is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def domain(self) -> str:
        """Get email domain"""
        return self.value.split('@')[1]
    
    def local_part(self) -> str:
        """Get local part of email (before @)"""
        return self.value.split('@')[0]
    
    def is_personal_domain(self) -> bool:
        """Check if email uses a personal domain (not corporate)"""
        personal_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com'}
        return self.domain() in personal_domains
    
    def __str__(self) -> str:
        return self.value