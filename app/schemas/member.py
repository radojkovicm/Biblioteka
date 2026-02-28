from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class MembershipOut(BaseModel):
    id: int
    member_id: int
    year: int
    amount_paid: float
    paid_at: date
    valid_from: date
    valid_until: date
    recorded_by: Optional[int] = None

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    member_number: int
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: str = "odrasli"
    allow_notifications: bool = True
    notes: Optional[str] = None


class MemberUpdate(BaseModel):
    member_number: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: Optional[str] = None
    allow_notifications: Optional[bool] = None
    notes: Optional[str] = None


class MemberOut(BaseModel):
    id: int
    member_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: str
    is_active: bool
    is_blocked: bool
    block_reason: Optional[str] = None
    allow_notifications: bool
    notes: Optional[str] = None
    registered_at: Optional[datetime] = None
    last_membership: Optional[MembershipOut] = None

    class Config:
        from_attributes = True


class MemberBlockRequest(BaseModel):
    is_blocked: bool
    block_reason: Optional[str] = None


class MembershipCreate(BaseModel):
    year: int
    amount_paid: float
    paid_at: date
    valid_from: date
    valid_until: date
