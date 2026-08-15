"""
Pydantic schemas for BloodBank responses.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BloodBankResponse(BaseModel):
    """Public representation of a nearby blood bank, with computed distance."""

    id: int
    name: str
    phone: str
    latitude: float
    longitude: float
    verified: bool
    distance_km: float = Field(
        ...,
        description="Haversine distance in kilometres from the query origin.",
    )

    model_config = {"from_attributes": True}
