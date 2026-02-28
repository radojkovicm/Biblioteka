from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from app.database import Base


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    module = Column(Text, nullable=False)  # books|members|reservations|reports|settings|finance
    can_read = Column(Boolean, default=False)
    can_write = Column(Boolean, default=False)
