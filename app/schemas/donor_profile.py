"""
Pydantic schemas for DonorProfile create / update / response.
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.donor_profile import VerificationStatus

# ---------------------------------------------------------------------------
# Allowed blood types
# ---------------------------------------------------------------------------

_VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


# ---------------------------------------------------------------------------
# Create / update
# ---------------------------------------------------------------------------


class DonorProfileCreate(BaseModel):
    """Payload for POST /donors/profile — creates or fully replaces a profile."""

    blood_type: str = Field(..., examples=["O+"])
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in _VALID_BLOOD_TYPES:
            raise ValueError(
                f"blood_type must be one of {sorted(_VALID_BLOOD_TYPES)}"
            )
        return v


class DonorProfileUpdate(BaseModel):
    """Payload for partial updates (all fields optional)."""

    blood_type: Optional[str] = Field(None, examples=["A-"])
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if v not in _VALID_BLOOD_TYPES:
            raise ValueError(
                f"blood_type must be one of {sorted(_VALID_BLOOD_TYPES)}"
            )
        return v


class AvailabilityUpdate(BaseModel):
    """Payload for PATCH /donors/availability."""

    is_available: bool


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class DonorProfileResponse(BaseModel):
    """Public-safe representation of a donor profile."""

    id: int
    user_id: int
    blood_type: str
    latitude: float
    longitude: float
    is_available: bool
    verification_status: VerificationStatus
    last_donation_date: Optional[date] = None
    next_eligible_date: Optional[date] = None
    id_document_path: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Donation history item (public — no sensitive donor fields)
# ---------------------------------------------------------------------------


class DonationHistoryItem(BaseModel):
    """A single donation record, safe to expose publicly."""

    id: int
    date: date
    hospital_name: str
    units: int

    model_config = {"from_attributes": True}
