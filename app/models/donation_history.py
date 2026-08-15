import enum
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfirmedBy(str, enum.Enum):
    self_ = "self"
    hospital = "hospital"


class DonationHistory(Base):
    __tablename__ = "donation_history"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("donor_profiles.id"), nullable=False)
    date = Column(Date, nullable=False)
    hospital_name = Column(String(200), nullable=False)
    confirmed_by = Column(Enum(ConfirmedBy), nullable=False)
    units = Column(Integer, nullable=False)

    # Relationships
    donor = relationship("DonorProfile", back_populates="donation_history")
