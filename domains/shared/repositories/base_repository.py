from core.patterns.repository import IRepository
from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC

T = TypeVar('T')
ID = TypeVar('ID')

class BaseRepository(IRepository[T, ID], ABC, Generic[T, ID]):
    """Base repository with common functionality"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    async def exists(self, id: ID) -> bool:
        entity = await self.find_by_id(id)
        return entity is not None