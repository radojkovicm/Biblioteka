from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from app.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    action = Column(Text, nullable=False)  # CREATE|UPDATE|DELETE|LOGIN|LOGOUT|EXPORT
    entity = Column(Text, nullable=False)  # member|book|loan|reservation|membership...
    entity_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
