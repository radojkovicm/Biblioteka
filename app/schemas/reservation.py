from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReservationCreate(BaseModel):
    book_id: int
    member_id: int


class ReservationOut(BaseModel):
    id: int
    book_id: int
    member_id: int
    reserved_at: Optional[datetime] = None
    queue_position: int
    status: str
    notified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    # joined fields
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    member_name: Optional[str] = None
    member_number: Optional[str] = None

    class Config:
        from_attributes = True
