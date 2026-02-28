from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: str = "odrasli"
    notes: Optional[str] = None


class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    member_type: Optional[str] = None
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
    notes: Optional[str] = None
    registered_at: Optional[datetime] = None

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
