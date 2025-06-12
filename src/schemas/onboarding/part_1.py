from typing import List, Optional
from pydantic import BaseModel, Field
from ...models.enums import NativeLanguage, Industry
from ..base import BaseResponse


class NativeLanguageRequest(BaseModel):
    native_language: NativeLanguage


class NativeLanguageResponse(BaseResponse):
    message: str
    native_language: NativeLanguage


class IndustryRequest(BaseModel):
    industry: Industry


class IndustryResponse(BaseResponse):
    message: str
    industry: Industry


class RoleSearchRequest(BaseModel):
    job_title: str = Field(..., min_length=2, max_length=200)
    job_description: str = Field(..., min_length=10, max_length=1000)


class RoleMatch(BaseModel):
    id: str
    title: str
    description: str
    industry_name: str
    confidence_score: float


class RoleSearchResponse(BaseResponse):
    matches: List[RoleMatch]
    search_id: Optional[str] = None  # For tracking purposes


class RoleSelectionRequest(BaseModel):
    role_id: Optional[str] = None  # None if no match selected
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None


class RoleSelectionResponse(BaseResponse):
    message: str
    role_id: Optional[str] = None
    is_custom: bool = False