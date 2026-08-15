"""
Donor matching service.

Provides two public functions:

- ``get_compatible_donor_types(blood_type_needed)``
  Returns the list of blood types whose donors CAN donate to a patient who
  needs *blood_type_needed*.  Direction: donor → patient.

- ``find_candidate_donors(db, blood_type_needed, lat, lng, radius_km)``
  Queries DonorProfile for eligible, verified, available donors whose blood
  type is compatible, filtered to within *radius_km* using the Haversine
  formula, ordered nearest-first, limited to 10.
"""
from __future__ import annotations

from datetime import date
from math import radians
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.donor_profile import DonorProfile

# ---------------------------------------------------------------------------
# Compatibility matrix
#
# Key  : blood type NEEDED by the patient (recipient)
# Value: list of donor blood types that CAN safely donate to that recipient
#
# Standard ABO/Rh compatibility rules:
#   - O- is the universal donor (can give to anyone)
#   - AB+ is the universal recipient (can receive from anyone)
#   - Rh-negative recipients can only receive Rh-negative blood
#   - ABO compatibility: O donors give to anyone in their Rh group;
#     A donors give to A/AB; B donors give to B/AB; AB donors give only to AB
# ---------------------------------------------------------------------------

_COMPATIBILITY: dict[str, list[str]] = {
    "A+":  ["A+", "A-", "O+", "O-"],
    "A-":  ["A-", "O-"],
    "B+":  ["B+", "B-", "O+", "O-"],
    "B-":  ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],  # universal recipient
    "AB-": ["A-", "B-", "AB-", "O-"],
    "O+":  ["O+", "O-"],
    "O-":  ["O-"],   # universal donor — only O- donors are compatible
}


def get_compatible_donor_types(blood_type_needed: str) -> list[str]:
    """
    Return the donor blood types compatible with *blood_type_needed*.

    The question answered is: "which donor types CAN give blood to a patient
    who needs *blood_type_needed*?"

    Input is accepted as-is (no normalisation); callers are responsible for
    passing a correctly-cased string (e.g. the schema validators upstream
    already call ``.strip().upper()`` before this function is reached).

    Args:
        blood_type_needed: The recipient's (patient's) blood type, e.g. ``"A+"``.

    Returns:
        List of donor blood type strings.  The list preserves insertion order
        (most-compatible first).

    Raises:
        ValueError: If *blood_type_needed* is not a recognised blood type.
    """
    if blood_type_needed not in _COMPATIBILITY:
        raise ValueError(
            f"Unknown blood type '{blood_type_needed}'. "
            f"Must be one of: {sorted(_COMPATIBILITY.keys())}"
        )
    return list(_COMPATIBILITY[blood_type_needed])


# ---------------------------------------------------------------------------
# Haversine query
# ---------------------------------------------------------------------------

# The Haversine formula, expressed as a SQL fragment that works in both
# PostgreSQL (production) and SQLite (tests).
#
# earth_radius * acos(
#     sin(lat1) * sin(lat2) +
#     cos(lat1) * cos(lat2) * cos(lng2 - lng1)
# )
#
# All trig functions work identically in both databases; ACOS is standard SQL.
# Input coordinates are stored as degrees, so we convert via (x * pi / 180).
#
# NOTE on IN-list binding:
# SQLite's pysqlite driver does not support binding a tuple/list as a single
# parameter for "IN (?)".  We must expand the list into individual named
# parameters (:bt0, :bt1, …) and interpolate their placeholders directly into
# the SQL string.  This is safe because the values come exclusively from
# our own hard-coded _COMPATIBILITY dict — no user input reaches this path.

def _build_query(compatible: list[str]) -> tuple[str, dict]:
    """
    Build the Haversine candidate-search query and its parameter dict.

    Returns (sql_string, params_dict).  The IN-list is expanded into
    individual named parameters to stay compatible with SQLite's pysqlite
    driver.
    """
    # Expand blood types into named params: :bt0, :bt1, ...
    bt_params = {f"bt{i}": bt for i, bt in enumerate(compatible)}
    bt_placeholders = ", ".join(f":bt{i}" for i in range(len(compatible)))

    haversine = """
        6371.0 * acos(
            sin(:origin_lat_rad) * sin(latitude  * :deg2rad)
          + cos(:origin_lat_rad) * cos(latitude  * :deg2rad)
                                 * cos(longitude * :deg2rad - :origin_lng_rad)
        )
    """

    sql = f"""
        SELECT id
        FROM   donor_profiles
        WHERE  blood_type         IN ({bt_placeholders})
        AND    is_available        = 1
        AND    verification_status = 'verified'
        AND    (next_eligible_date IS NULL OR next_eligible_date <= :today)
        AND    {haversine} <= :radius_km
        ORDER  BY {haversine} ASC
        LIMIT  10
    """
    return sql, bt_params


def find_candidate_donors(
    db: Session,
    blood_type_needed: str,
    lat: float,
    lng: float,
    radius_km: float = 5.0,
) -> List[DonorProfile]:
    """
    Find eligible donor profiles compatible with *blood_type_needed* within
    *radius_km* of (lat, lng).

    Eligibility conditions:
    - ``blood_type`` is in the compatible donor list for *blood_type_needed*
    - ``is_available`` is ``True``
    - ``verification_status`` is ``'verified'``
    - ``next_eligible_date`` is NULL **or** <= today
    - within *radius_km* kilometres (Haversine distance)

    Results are ordered nearest-first and capped at 10.

    Args:
        db: SQLAlchemy session.
        blood_type_needed: The recipient's blood type (normalised, e.g. "A+").
        lat: Latitude of the request location (degrees).
        lng: Longitude of the request location (degrees).
        radius_km: Search radius in kilometres.  Defaults to 5.

    Returns:
        Ordered list of :class:`DonorProfile` ORM objects.
    """
    compatible = get_compatible_donor_types(blood_type_needed)

    deg2rad = radians(1)  # π/180  — converts degrees to radians
    origin_lat_rad = radians(lat)
    origin_lng_rad = radians(lng)

    sql, bt_params = _build_query(compatible)

    params: dict = {
        **bt_params,
        "today": date.today().isoformat(),
        "origin_lat_rad": origin_lat_rad,
        "origin_lng_rad": origin_lng_rad,
        "deg2rad": deg2rad,
        "radius_km": radius_km,
    }

    result = db.execute(text(sql), params)
    donor_ids: list[int] = [row[0] for row in result]

    if not donor_ids:
        return []

    # Re-fetch as ORM objects, preserving distance order
    id_to_donor: dict[int, DonorProfile] = {
        d.id: d
        for d in db.query(DonorProfile).filter(DonorProfile.id.in_(donor_ids)).all()
    }
    return [id_to_donor[did] for did in donor_ids if did in id_to_donor]
