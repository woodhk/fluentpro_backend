from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime, timezone


class BaseResponse(BaseModel):
    """Base response schema."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
