"""
Tests for GET /api/v1/blood-banks/nearby.

Uses the shared in-memory SQLite engine from conftest so no real database
connection is required.  The Haversine formula works identically in SQLite
and MySQL/PostgreSQL (acos/sin/cos are standard SQL).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.blood_bank import BloodBank
from tests.conftest import TestingSessionLocal

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Lahore city centre as the default search origin
_ORIGIN_LAT = 31.5204
_ORIGIN_LNG = 74.3587

# Approximate distances from origin:
#   _NEAR  ≈  1 km north
#   _MID   ≈  5 km north
#   _FAR   ≈ 25 km north  (outside default 20 km radius)
_NEAR = (31.5294, 74.3587)   # ~1 km
_MID  = (31.5654, 74.3587)   # ~5 km
_FAR  = (31.7454, 74.3587)   # ~25 km


def _add_bank(
    db,
    *,
    name: str,
    lat: float,
    lng: float,
    phone: str = "+92 300 0000000",
    verified: bool = True,
) -> BloodBank:
    bank = BloodBank(name=name, phone=phone, latitude=lat, longitude=lng, verified=verified)
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


# ---------------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------------


class TestNearbyValidation:
    def test_missing_lat_returns_422(self):
        r = client.get("/api/v1/blood-banks/nearby", params={"lng": 74.3587})
        assert r.status_code == 422

    def test_missing_lng_returns_422(self):
        r = client.get("/api/v1/blood-banks/nearby", params={"lat": 31.5204})
        assert r.status_code == 422

    def test_lat_out_of_range_returns_422(self):
        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": 100.0, "lng": 74.3587},
        )
        assert r.status_code == 422

    def test_lng_out_of_range_returns_422(self):
        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": 31.5204, "lng": 200.0},
        )
        assert r.status_code == 422

    def test_radius_zero_returns_422(self):
        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": 31.5204, "lng": 74.3587, "radius_km": 0},
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Core behaviour
# ---------------------------------------------------------------------------


class TestNearbyBloodBanks:
    def test_empty_db_returns_empty_list(self):
        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG},
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_verified_bank_within_radius_returned(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Near Verified", lat=_NEAR[0], lng=_NEAR[1])
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 10},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["name"] == "Near Verified"
        assert data[0]["verified"] is True
        assert "distance_km" in data[0]

    def test_bank_outside_radius_excluded(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Far Bank", lat=_FAR[0], lng=_FAR[1])
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 20},
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_unverified_bank_excluded(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Unverified", lat=_NEAR[0], lng=_NEAR[1], verified=False)
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 10},
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_results_ordered_nearest_first(self):
        db = TestingSessionLocal()
        try:
            # Insert farther one first to confirm sorting
            _add_bank(db, name="Mid Bank", lat=_MID[0], lng=_MID[1])
            _add_bank(db, name="Near Bank", lat=_NEAR[0], lng=_NEAR[1])
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 20},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["name"] == "Near Bank"
        assert data[1]["name"] == "Mid Bank"
        # Nearest should have the smaller distance_km
        assert data[0]["distance_km"] < data[1]["distance_km"]

    def test_distance_km_present_and_positive(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Test Bank", lat=_NEAR[0], lng=_NEAR[1])
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["distance_km"] > 0

    def test_default_radius_is_20_km(self):
        """A bank exactly 21 km away should be excluded when no radius_km is given."""
        # 21 km north ≈ lat + 0.189
        far_lat = _ORIGIN_LAT + 0.189   # ~21 km
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="21km Bank", lat=far_lat, lng=_ORIGIN_LNG)
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG},
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_custom_radius_expands_results(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Mid Bank", lat=_MID[0], lng=_MID[1])
        finally:
            db.close()

        # Should be excluded at 3 km radius
        r_small = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 3},
        )
        # Should be included at 10 km radius
        r_large = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 10},
        )

        assert r_small.status_code == 200
        assert r_large.status_code == 200
        assert len(r_small.json()) == 0
        assert len(r_large.json()) == 1

    def test_mixed_verified_and_unverified_only_verified_returned(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Verified A", lat=_NEAR[0], lng=_NEAR[1], verified=True)
            _add_bank(db, name="Unverified B", lat=_NEAR[0], lng=_NEAR[1], verified=False)
            _add_bank(db, name="Verified C", lat=_MID[0], lng=_MID[1], verified=True)
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 20},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert names == {"Verified A", "Verified C"}

    def test_response_schema_has_required_fields(self):
        db = TestingSessionLocal()
        try:
            _add_bank(db, name="Schema Test", lat=_NEAR[0], lng=_NEAR[1], phone="+92 42 1234567")
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG},
        )
        assert r.status_code == 200
        item = r.json()[0]
        for field in ("id", "name", "phone", "latitude", "longitude", "verified", "distance_km"):
            assert field in item, f"Missing field: {field}"

    def test_multiple_banks_all_within_radius(self):
        db = TestingSessionLocal()
        try:
            for i in range(5):
                _add_bank(
                    db,
                    name=f"Bank {i}",
                    lat=_NEAR[0] + i * 0.001,  # tiny offsets, all < 2 km
                    lng=_NEAR[1],
                )
        finally:
            db.close()

        r = client.get(
            "/api/v1/blood-banks/nearby",
            params={"lat": _ORIGIN_LAT, "lng": _ORIGIN_LNG, "radius_km": 20},
        )
        assert r.status_code == 200
        assert len(r.json()) == 5
