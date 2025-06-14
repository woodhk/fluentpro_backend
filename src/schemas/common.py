from pydantic import BaseModel, Field, ConfigDict
from typing import TypeVar, Generic, List, Optional, Any, Dict
from datetime import datetime, timezone

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    data: List[T]
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: Optional[str] = None


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps."""

    created_at: datetime
    updated_at: datetime


class SortParams(BaseModel):
    """Common sorting parameters."""

    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(
        default="desc", regex="^(asc|desc)$", description="Sort order"
    )


class FilterParams(BaseModel):
    """Base class for filter parameters."""

    search: Optional[str] = Field(None, description="Search term")

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional fields for specific filters


class BatchOperationResult(BaseModel):
    """Result of a batch operation."""

    total: int
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]] = []


class IdResponse(BaseModel):
    """Response containing only an ID."""

    id: str


class CountResponse(BaseModel):
    """Response containing a count."""

    count: int


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""

    field: str
    message: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""

    error: str = "validation_error"
    message: str = "Validation failed"
    details: List[ValidationErrorDetail]


# Import Dict for backwards compatibility
from typing import Dict
