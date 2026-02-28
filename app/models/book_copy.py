from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, Date, ForeignKey
from app.database import Base


class BookCopy(Base):
    __tablename__ = "book_copies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    library_number = Column(Text, unique=True, nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(Text, default="available")  # available|loaned|reserved|damaged|lost
    shelf_location = Column(Text, nullable=True)
    condition = Column(Text, default="good")  # good|damaged|poor
    acquisition_type = Column(Text, default="donation")  # purchase|donation|transfer
    acquired_at = Column(Date, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
