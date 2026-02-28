from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    is_admin: bool


class StaffCreate(BaseModel):
    username: str
    full_name: str
    password: str
    is_admin: bool = False


class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class StaffOut(BaseModel):
    id: int
    username: str
    full_name: str
    is_admin: bool
    is_active: bool
    last_login: Optional[str] = None

    class Config:
        from_attributes = True
