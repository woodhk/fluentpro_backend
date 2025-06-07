from core.patterns.value_object import ValueObject
from core.utils.validation_utils import validate_phone_number
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    value: str
    
    def _validate(self):
        if not validate_phone_number(self.value):
            raise ValueError(f"Invalid phone number format: {self.value}")
    
    def normalized(self) -> str:
        """Get normalized phone number (digits only)"""
        return re.sub(r'\D', '', self.value)
    
    def formatted(self, format_type: str = 'international') -> str:
        """Format phone number"""
        digits = self.normalized()
        
        if format_type == 'international':
            if len(digits) == 10:  # US number
                return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits.startswith('1'):  # US number with country code
                return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                return f"+{digits}"
        
        elif format_type == 'national':
            if len(digits) >= 10:
                local_digits = digits[-10:]
                return f"({local_digits[:3]}) {local_digits[3:6]}-{local_digits[6:]}"
            else:
                return self.value
        
        return self.value
    
    def country_code(self) -> str:
        """Extract country code if present"""
        digits = self.normalized()
        if len(digits) > 10:
            return digits[:-10]
        return "1"  # Default to US
    
    def __str__(self) -> str:
        return self.formatted()