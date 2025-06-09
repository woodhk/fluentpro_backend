from pydantic import BaseModel
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