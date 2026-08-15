from sqlalchemy import Column, Integer, String, Float, Boolean
from app.core.database import Base


class BloodBank(Base):
    __tablename__ = "blood_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
