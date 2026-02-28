from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime


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
    last_login: Optional[datetime] = None

    @field_serializer('last_login')
    def serialize_last_login(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat()

    class Config:
        from_attributes = True
