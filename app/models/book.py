from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, DateTime
from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    author = Column(Text, nullable=False)
    publisher = Column(Text, nullable=True)
    year_published = Column(Integer, nullable=True)
    genre = Column(Text, nullable=True)
    language = Column(Text, default="srpski")
    description = Column(Text, nullable=True)
    total_copies = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
