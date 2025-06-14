from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, date
from typing import Optional


class UserBase(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None


class UserCreate(UserBase):
    auth0_id: str
    email: EmailStr
    is_active: bool = True


class UserUpdate(UserBase):
    pass


class UserResponse(UserBase):
    id: str
    auth0_id: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    id: str
    full_name: Optional[str]
    email: EmailStr
    date_of_birth: Optional[date]
    is_active: bool
