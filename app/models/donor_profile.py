import enum
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class DonorProfile(Base):
    __tablename__ = "donor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    blood_type = Column(String(5), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_donation_date = Column(Date, nullable=True)
    next_eligible_date = Column(Date, nullable=True)
    is_available = Column(Boolean, default=False, nullable=False)
    verification_status = Column(
        Enum(VerificationStatus), default=VerificationStatus.pending, nullable=False
    )
    id_document_path = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="donor_profile")
    request_matches = relationship("RequestMatch", back_populates="donor")
    donation_history = relationship("DonationHistory", back_populates="donor")
