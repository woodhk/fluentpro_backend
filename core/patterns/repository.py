from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar('T')  # Entity type
ID = TypeVar('ID')  # ID type

class IRepository(ABC, Generic[T, ID]):
    """Base repository interface for all repositories"""
    
    @abstractmethod
    async def find_by_id(self, id: ID) -> Optional[T]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Find all entities matching filters"""
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)"""
        pass
    
    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete entity by ID"""
        pass
    
    @abstractmethod
    async def exists(self, id: ID) -> bool:
        """Check if entity exists"""
        pass