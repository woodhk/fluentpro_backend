from abc import ABC
from typing import Any
from dataclasses import dataclass

@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for value objects - immutable domain objects"""
    
    def __post_init__(self):
        """Validate after initialization"""
        self._validate()
    
    def _validate(self):
        """Override to add validation logic"""
        pass
    
    def equals(self, other: Any) -> bool:
        """Value equality comparison"""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__