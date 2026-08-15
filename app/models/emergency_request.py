import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class UrgencyLevel(str, enum.Enum):
    critical = "critical"
    urgent = "urgent"
    planned = "planned"


class RequestStatus(str, enum.Enum):
    open = "open"
    matched = "matched"
    fulfilled = "fulfilled"
    expired = "expired"


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_type_needed = Column(String(5), nullable=False)
    units_needed = Column(Integer, nullable=False)
    hospital_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    urgency_level = Column(Enum(UrgencyLevel), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.open, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    requester = relationship("User", back_populates="emergency_requests")
    matches = relationship("RequestMatch", back_populates="request")
