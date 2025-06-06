"""
Base Repository Interface

Provides generic repository pattern interface for domain entities.
All domain repositories should extend this base interface.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any

# Generic type for entities
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Generic base repository interface providing CRUD operations.
    
    All domain repositories should extend this interface and add
    domain-specific query methods.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its unique identifier.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Retrieve all entities with optional pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    def create(self, entity_data: Dict[str, Any]) -> T:
        """
        Create a new entity.
        
        Args:
            entity_data: Dictionary containing entity data
            
        Returns:
            The created entity
            
        Raises:
            ValidationError: If entity data is invalid
        """
        pass
    
    @abstractmethod
    def update(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            entity_id: The unique identifier of the entity
            entity_data: Dictionary containing updated data
            
        Returns:
            The updated entity if found, None otherwise
            
        Raises:
            ValidationError: If entity data is invalid
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by its identifier.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            True if entity was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: The unique identifier of the entity
            
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            filters: Optional dictionary of filter criteria
            
        Returns:
            Number of matching entities
        """
        pass
    
    @abstractmethod
    def find(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """
        Find entities matching the given criteria.
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of entities to return
            
        Returns:
            List of matching entities
        """
        pass


class TransactionalRepository(BaseRepository[T]):
    """
    Extended repository interface supporting transactional operations.
    
    Used when repository operations need to participate in
    unit of work transactions.
    """
    
    @abstractmethod
    def begin_transaction(self):
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    def commit(self):
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self):
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    def in_transaction(self) -> bool:
        """Check if currently in a transaction."""
        pass


class CachedRepository(BaseRepository[T]):
    """
    Repository interface with caching support.
    
    Provides cache-aware methods for improved performance.
    """
    
    @abstractmethod
    def get_by_id_cached(self, entity_id: str, cache_timeout: int = 300) -> Optional[T]:
        """
        Retrieve an entity by ID with caching.
        
        Args:
            entity_id: The unique identifier of the entity
            cache_timeout: Cache timeout in seconds
            
        Returns:
            The cached or fresh entity if found
        """
        pass
    
    @abstractmethod
    def invalidate_cache(self, entity_id: str):
        """
        Invalidate cache for a specific entity.
        
        Args:
            entity_id: The unique identifier of the entity
        """
        pass
    
    @abstractmethod
    def invalidate_all_cache(self):
        """Invalidate all cached entries for this repository."""
        pass