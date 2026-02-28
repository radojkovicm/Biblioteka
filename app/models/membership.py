from sqlalchemy import Column, Integer, Text, Date, Float, ForeignKey
from app.database import Base


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    year = Column(Integer, nullable=False)
    amount_paid = Column(Float, nullable=False)
    paid_at = Column(Date, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)
    recorded_by = Column(Integer, ForeignKey("staff.id"), nullable=True)
