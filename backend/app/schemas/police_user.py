from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PoliceUserCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    password: str
    badge_number: Optional[str] = None
    role: str  # admin / supervisor / officer
    assigned_location_id: Optional[int] = None


class PoliceUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    badge_number: Optional[str] = None
    role: Optional[str] = None
    assigned_location_id: Optional[int] = None
    is_active: Optional[bool] = None


class PoliceUserResponse(BaseModel):
    police_user_id: int
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    phone_number: Optional[str]
    badge_number: Optional[str]
    role: str
    assigned_location_id: Optional[int]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True
