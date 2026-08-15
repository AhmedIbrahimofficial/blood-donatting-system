import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class MatchStatus(str, enum.Enum):
    notified = "notified"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class RequestMatch(Base):
    __tablename__ = "request_matches"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("emergency_requests.id"), nullable=False)
    donor_id = Column(Integer, ForeignKey("donor_profiles.id"), nullable=False)
    status = Column(Enum(MatchStatus), default=MatchStatus.notified, nullable=False)
    notified_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    request = relationship("EmergencyRequest", back_populates="matches")
    donor = relationship("DonorProfile", back_populates="request_matches")
