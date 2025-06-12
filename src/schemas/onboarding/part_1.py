from pydantic import BaseModel
from ...models.enums import NativeLanguage
from ..base import BaseResponse


class NativeLanguageRequest(BaseModel):
    native_language: NativeLanguage


class NativeLanguageResponse(BaseResponse):
    message: str
    native_language: NativeLanguage