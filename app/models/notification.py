from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Boolean
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_type = Column(Text, nullable=False)  # due_tomorrow|due_today|overdue|reservation_available|membership_expiring|membership_expired
    entity_id = Column(Integer, nullable=False)  # loan_id or member_id depending on trigger
    member_id = Column(Integer, nullable=False)
    email_to = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
