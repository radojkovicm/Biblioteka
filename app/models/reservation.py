from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    queue_position = Column(Integer, default=1)
    status = Column(Text, default="waiting")  # waiting|notified|fulfilled|cancelled
    notified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
