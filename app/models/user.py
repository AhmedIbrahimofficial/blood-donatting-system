import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    donor = "donor"
    requester = "requester"
    both = "both"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True, index=True)  # stored from Google OAuth
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    phone_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    donor_profile = relationship("DonorProfile", back_populates="user", uselist=False)
    emergency_requests = relationship("EmergencyRequest", back_populates="requester")
