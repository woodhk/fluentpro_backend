from pydantic import BaseModel
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