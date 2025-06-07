from core.patterns.value_object import ValueObject
from core.utils.validation_utils import is_strong_password
from dataclasses import dataclass

@dataclass(frozen=True)
class Password(ValueObject):
    value: str
    
    def _validate(self):
        is_valid, error_message = is_strong_password(self.value)
        if not is_valid:
            raise ValueError(error_message)
    
    def strength_score(self) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        if len(self.value) >= 8:
            score += 20
        if len(self.value) >= 12:
            score += 10
        if len(self.value) >= 16:
            score += 10
        
        # Character variety
        import re
        if re.search(r'[A-Z]', self.value):
            score += 15
        if re.search(r'[a-z]', self.value):
            score += 15
        if re.search(r'\d', self.value):
            score += 15
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', self.value):
            score += 15
        
        return min(score, 100)
    
    def __str__(self) -> str:
        return "***HIDDEN***"