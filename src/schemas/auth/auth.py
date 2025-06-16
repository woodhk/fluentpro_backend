from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class TokenPayload(BaseModel):
    sub: str  # Auth0 user ID
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class AuthStatus(BaseModel):
    authenticated: bool
    user_id: Optional[str] = None
    message: str


class Auth0WebhookPayload(BaseModel):
    event: str
    user: Dict[str, Any]


class UserCreatedWebhook(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class SignupResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    user: Dict[str, Any]
