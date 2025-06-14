from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from supabase import Client

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository class for data access operations."""

    def __init__(self, db: Client, table_name: str):
        self.db = db
        self.table_name = table_name

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        pass

    @abstractmethod
    async def get_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all records with optional filters."""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete a record by ID."""
        pass

    async def exists(self, id: str) -> bool:
        """Check if a record exists by ID."""
        result = await self.get_by_id(id)
        return result is not None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = self.db.table(self.table_name).select("id", count="exact")

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.execute()
        return result.count if result.count is not None else 0


class SupabaseRepository(BaseRepository[T]):
    """Concrete implementation of BaseRepository for Supabase."""

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID from Supabase."""
        result = self.db.table(self.table_name).select("*").eq("id", id).execute()
        return result.data[0] if result.data else None

    async def get_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all records from Supabase with optional filters."""
        query = self.db.table(self.table_name).select("*")

        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)

        result = query.execute()
        return result.data or []

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in Supabase."""
        result = self.db.table(self.table_name).insert(data).execute()
        if not result.data:
            raise Exception(f"Failed to create record in {self.table_name}")
        return result.data[0]

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record in Supabase."""
        result = self.db.table(self.table_name).update(data).eq("id", id).execute()
        return result.data[0] if result.data else None

    async def delete(self, id: str) -> bool:
        """Delete a record from Supabase."""
        result = self.db.table(self.table_name).delete().eq("id", id).execute()
        return len(result.data) > 0 if result.data else False

    async def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by a specific field."""
        result = self.db.table(self.table_name).select("*").eq(field, value).execute()
        return result.data[0] if result.data else None

    async def get_many_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Get multiple records by a specific field."""
        result = self.db.table(self.table_name).select("*").eq(field, value).execute()
        return result.data or []

    async def search(self, field: str, pattern: str) -> List[Dict[str, Any]]:
        """Search records by pattern matching on a field."""
        result = (
            self.db.table(self.table_name)
            .select("*")
            .ilike(field, f"%{pattern}%")
            .execute()
        )
        return result.data or []

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = "created_at",
        order_desc: bool = True,
    ) -> Dict[str, Any]:
        """Get paginated results."""
        offset = (page - 1) * page_size

        query = self.db.table(self.table_name).select("*", count="exact")

        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)

        if order_by:
            query = query.order(order_by, desc=order_desc)

        query = query.range(offset, offset + page_size - 1)
        result = query.execute()

        total_count = result.count or 0
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "data": result.data or [],
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
