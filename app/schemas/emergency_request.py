"""
Pydantic schemas for EmergencyRequest create / response.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.emergency_request import RequestStatus, UrgencyLevel
from app.models.request_match import MatchStatus

_VALID_BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


# ---------------------------------------------------------------------------
# Request (create)
# ---------------------------------------------------------------------------


class EmergencyRequestCreate(BaseModel):
    """Payload for POST /api/v1/requests."""

    blood_type_needed: str = Field(..., examples=["O+"])
    units_needed: int = Field(..., ge=1, le=20)
    hospital_name: str = Field(..., min_length=2, max_length=200)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    urgency_level: UrgencyLevel
    radius_km: float = Field(default=5.0, ge=0.1, le=100.0)

    @field_validator("blood_type_needed")
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in _VALID_BLOOD_TYPES:
            raise ValueError(
                f"blood_type_needed must be one of {sorted(_VALID_BLOOD_TYPES)}"
            )
        return v


# ---------------------------------------------------------------------------
# Nested schemas used in responses
# ---------------------------------------------------------------------------


class RequestMatchResponse(BaseModel):
    """A single match record associated with an emergency request."""

    id: int
    donor_id: int
    status: MatchStatus
    notified_at: datetime
    responded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class EmergencyRequestResponse(BaseModel):
    """Response after creating a new emergency request (legacy, sync path)."""

    id: int
    requester_id: int
    blood_type_needed: str
    units_needed: int
    hospital_name: str
    latitude: float
    longitude: float
    urgency_level: UrgencyLevel
    status: RequestStatus
    created_at: datetime
    candidates_found: int

    model_config = {"from_attributes": True}


class EmergencyRequestAcceptedResponse(BaseModel):
    """
    Immediate 202 response after creating a new emergency request.

    Matching and notification are handled asynchronously by Celery.
    Poll ``GET /api/v1/requests/{id}/status`` for updates.
    """

    id: int
    status: RequestStatus
    message: str

    model_config = {"from_attributes": True}


class EmergencyRequestStatusResponse(BaseModel):
    """Response for GET /api/v1/requests/{id}/status."""

    id: int
    status: RequestStatus
    blood_type_needed: str
    urgency_level: UrgencyLevel
    created_at: datetime
    matches: List[RequestMatchResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
