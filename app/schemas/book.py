from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class BookCreate(BaseModel):
    title: str
    author: str
    publisher: Optional[str] = None
    year_published: Optional[int] = None
    genre: Optional[str] = None
    language: str = "srpski"
    description: Optional[str] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    year_published: Optional[int] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    publisher: Optional[str] = None
    year_published: Optional[int] = None
    genre: Optional[str] = None
    language: str
    description: Optional[str] = None
    total_copies: int
    available_copies: int = 0

    class Config:
        from_attributes = True


class BookCopyCreate(BaseModel):
    library_number: str
    shelf_location: Optional[str] = None
    condition: str = "good"
    acquisition_type: str = "donation"
    acquired_at: Optional[date] = None
    notes: Optional[str] = None


class BookCopyUpdate(BaseModel):
    shelf_location: Optional[str] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BookCopyOut(BaseModel):
    id: int
    library_number: str
    book_id: int
    status: str
    shelf_location: Optional[str] = None
    condition: str
    acquisition_type: str
    acquired_at: Optional[date] = None
    notes: Optional[str] = None
    is_deleted: bool

    class Config:
        from_attributes = True


class BookDetailOut(BookOut):
    copies: List[BookCopyOut] = []
