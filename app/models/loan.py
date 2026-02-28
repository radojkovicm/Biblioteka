from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Date, ForeignKey
from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    copy_id = Column(Integer, ForeignKey("book_copies.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    loaned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    status = Column(Text, default="active")  # active|returned|overdue|lost
    extensions_count = Column(Integer, default=0)
    issued_by = Column(Integer, ForeignKey("staff.id"), nullable=True)
    returned_to = Column(Integer, ForeignKey("staff.id"), nullable=True)
