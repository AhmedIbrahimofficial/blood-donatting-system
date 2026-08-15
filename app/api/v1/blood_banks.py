"""
Blood bank endpoints.

Routes
------
GET /api/v1/blood-banks/nearby
    Returns verified BloodBank records within ``radius_km`` of the supplied
    (lat, lng) coordinate, ordered nearest-first.  Uses the same Haversine
    SQL formula as the donor matching service so behaviour is consistent
    across SQLite (tests) and MySQL/PostgreSQL (production).
"""
from __future__ import annotations

from math import radians
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.models.blood_bank import BloodBank
from app.schemas.blood_bank import BloodBankResponse

router = APIRouter(prefix="/api/v1/blood-banks", tags=["blood-banks"])


# ---------------------------------------------------------------------------
# Haversine helper — mirrors matching_service._build_query exactly
# ---------------------------------------------------------------------------

_HAVERSINE = """
    6371.0 * acos(
        sin(:origin_lat_rad) * sin(latitude  * :deg2rad)
      + cos(:origin_lat_rad) * cos(latitude  * :deg2rad)
                             * cos(longitude * :deg2rad - :origin_lng_rad)
    )
"""


def _nearby_ids_with_distances(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float,
) -> list[tuple[int, float]]:
    """
    Execute the Haversine query against ``blood_banks`` and return a list of
    ``(id, distance_km)`` tuples ordered nearest-first.

    Only rows where ``verified = 1`` are considered.
    """
    deg2rad = radians(1)  # π/180
    origin_lat_rad = radians(lat)
    origin_lng_rad = radians(lng)

    sql = f"""
        SELECT id, {_HAVERSINE} AS distance_km
        FROM   blood_banks
        WHERE  verified = 1
        AND    {_HAVERSINE} <= :radius_km
        ORDER  BY distance_km ASC
    """

    params = {
        "origin_lat_rad": origin_lat_rad,
        "origin_lng_rad": origin_lng_rad,
        "deg2rad": deg2rad,
        "radius_km": radius_km,
    }

    rows = db.execute(text(sql), params).fetchall()
    return [(row[0], round(row[1], 3)) for row in rows]


# ---------------------------------------------------------------------------
# GET /nearby
# ---------------------------------------------------------------------------


@router.get(
    "/nearby",
    response_model=List[BloodBankResponse],
    status_code=200,
    summary="Find verified blood banks within a radius",
)
@limiter.limit("60/minute")
def get_nearby_blood_banks(
    request: Request,
    lat: Annotated[float, Query(ge=-90.0, le=90.0, description="Origin latitude")],
    lng: Annotated[float, Query(ge=-180.0, le=180.0, description="Origin longitude")],
    radius_km: Annotated[
        float, Query(ge=0.1, le=500.0, description="Search radius in kilometres"),
    ] = 20.0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max results")] = 50,
    db: Annotated[Session, Depends(get_db)] = None,
) -> List[BloodBankResponse]:
    """
    Return all **verified** blood banks within *radius_km* kilometres of
    (*lat*, *lng*), ordered by ascending distance.

    Query parameters
    ----------------
    lat       : float  — origin latitude  (required)
    lng       : float  — origin longitude (required)
    radius_km : float  — search radius in km, default 20, max 500

    Response
    --------
    Each item includes all BloodBank fields plus a computed ``distance_km``
    field (rounded to 3 decimal places).  Returns an empty list when no
    verified banks are found within the radius.
    """
    id_dist_pairs = _nearby_ids_with_distances(db, lat, lng, radius_km)

    if not id_dist_pairs:
        return []

    # Apply limit
    id_dist_pairs = id_dist_pairs[:limit]

    ids = [row[0] for row in id_dist_pairs]
    dist_map: dict[int, float] = {row[0]: row[1] for row in id_dist_pairs}

    banks: dict[int, BloodBank] = {
        b.id: b
        for b in db.query(BloodBank).filter(BloodBank.id.in_(ids)).all()
    }

    result: List[BloodBankResponse] = []
    for bank_id in ids:
        bank = banks.get(bank_id)
        if bank is None:
            continue
        result.append(
            BloodBankResponse(
                id=bank.id,
                name=bank.name,
                phone=bank.phone,
                latitude=bank.latitude,
                longitude=bank.longitude,
                verified=bank.verified,
                distance_km=dist_map[bank_id],
            )
        )

    return result
