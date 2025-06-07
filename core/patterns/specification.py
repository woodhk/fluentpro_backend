from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')

class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        pass
    
    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        return OrSpecification(self, other)


class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(Specification[T]):
    def __init__(self, specification: Specification[T]):
        self.specification = specification
    
    def is_satisfied_by(self, entity: T) -> bool:
        return not self.specification.is_satisfied_by(entity)