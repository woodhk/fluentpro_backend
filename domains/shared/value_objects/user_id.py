from core.patterns.value_object import ValueObject
from dataclasses import dataclass
import uuid

@dataclass(frozen=True)
class UserId(ValueObject):
    value: str
    
    def _validate(self):
        if not self.value:
            raise ValueError("User ID cannot be empty")
        
        # Validate UUID format for internal IDs
        if self.value.startswith('user_'):
            uuid_part = self.value[5:]
            try:
                uuid.UUID(uuid_part)
            except ValueError:
                raise ValueError(f"Invalid internal user ID format: {self.value}")
        
        # Validate Auth0 ID format
        elif self.value.startswith('auth0|'):
            if len(self.value) < 10:
                raise ValueError(f"Invalid Auth0 user ID format: {self.value}")
        
        else:
            # Generic validation for other ID formats
            if len(self.value) < 3 or len(self.value) > 255:
                raise ValueError(f"User ID must be between 3 and 255 characters: {self.value}")
    
    def is_auth0_id(self) -> bool:
        """Check if this is an Auth0 user ID"""
        return self.value.startswith('auth0|')
    
    def is_internal_id(self) -> bool:
        """Check if this is an internal user ID"""
        return self.value.startswith('user_')
    
    def __str__(self) -> str:
        return self.value