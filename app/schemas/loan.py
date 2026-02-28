from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class LoanCreate(BaseModel):
    copy_id: int
    member_id: int


class LoanOut(BaseModel):
    id: int
    copy_id: int
    member_id: int
    loaned_at: Optional[datetime] = None
    due_date: date
    returned_at: Optional[datetime] = None
    status: str
    extensions_count: int
    issued_by: Optional[int] = None
    returned_to: Optional[int] = None
    # joined fields
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    library_number: Optional[str] = None
    member_name: Optional[str] = None
    member_number: Optional[str] = None

    class Config:
        from_attributes = True
