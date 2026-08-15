"""
Feature tests for /api/v1/donors endpoints.

Isolation strategy:
- Database : SQLite in-memory with StaticPool (shared via conftest)
- Auth     : mocked Google OAuth (no real Firebase call)
- Uploads  : temporary directory (patched via monkeypatch)
"""
import io
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.donor_profile import DonorProfile
from tests.conftest import TestingSessionLocal
from tests.helpers import google_login_mock, auth_headers as _auth_headers

client = TestClient(app)

# Counter to give each test its own unique Google UID
_uid = 0

def _next_token(name: str = "Donor") -> str:
    global _uid
    _uid += 1
    return google_login_mock(uid=f"donor_uid_{_uid:04d}", name=name)


def _create_profile(token: str, blood_type: str = "O+") -> dict:
    r = client.post(
        "/api/v1/donors/profile",
        data={"blood_type": blood_type, "latitude": "12.345", "longitude": "67.890"},
        headers=_auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()


def _set_next_eligible(user_id: int, next_eligible: date | None) -> None:
    db = TestingSessionLocal()
    try:
        profile = db.query(DonorProfile).filter(DonorProfile.user_id == user_id).first()
        assert profile is not None
        profile.next_eligible_date = next_eligible
        db.commit()
    finally:
        db.close()


def _get_user_id(token: str) -> int:
    from app.core.security import decode_access_token
    return int(decode_access_token(token)["sub"])


# ---------------------------------------------------------------------------
# 1. Create profile succeeds
# ---------------------------------------------------------------------------

class TestCreateProfile:
    def test_create_profile_returns_200_and_profile(self):
        token = _next_token()
        r = client.post(
            "/api/v1/donors/profile",
            data={"blood_type": "A+", "latitude": "51.5074", "longitude": "-0.1278"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["blood_type"] == "A+"
        assert data["latitude"] == pytest.approx(51.5074)
        assert data["longitude"] == pytest.approx(-0.1278)
        assert data["verification_status"] == "pending"
        assert data["is_available"] is False

    def test_create_profile_with_id_document(self, tmp_path, monkeypatch):
        """Uploading an id_document saves the file and records the path."""
        monkeypatch.setattr("app.api.v1.donors._UPLOAD_DIR", str(tmp_path))
        token = _next_token()
        fake_file = io.BytesIO(b"fake pdf content")
        r = client.post(
            "/api/v1/donors/profile",
            data={"blood_type": "B-", "latitude": "0.0", "longitude": "0.0"},
            files={"id_document": ("id.pdf", fake_file, "application/pdf")},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["id_document_path"] is not None
        # Filename is renamed to a UUID; original name should not appear
        assert "id.pdf" not in data["id_document_path"]

    def test_upsert_profile_updates_existing(self):
        token = _next_token()
        _create_profile(token, blood_type="O+")

        r = client.post(
            "/api/v1/donors/profile",
            data={"blood_type": "AB-", "latitude": "10.0", "longitude": "20.0"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["blood_type"] == "AB-"

    def test_create_profile_invalid_blood_type_returns_422(self):
        token = _next_token()
        r = client.post(
            "/api/v1/donors/profile",
            data={"blood_type": "Z+", "latitude": "0.0", "longitude": "0.0"},
            headers=_auth_headers(token),
        )
        assert r.status_code == 422

    def test_get_profile_returns_created_profile(self):
        token = _next_token()
        _create_profile(token, blood_type="O-")
        r = client.get("/api/v1/donors/profile", headers=_auth_headers(token))
        assert r.status_code == 200
        assert r.json()["blood_type"] == "O-"


# ---------------------------------------------------------------------------
# 2 & 3. Toggle availability — success cases
# ---------------------------------------------------------------------------

class TestAvailabilityToggleSuccess:
    def test_toggle_available_true_when_no_eligibility_date(self):
        """is_available=True succeeds when next_eligible_date is NULL."""
        token = _next_token()
        _create_profile(token)

        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": True},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["is_available"] is True

    def test_toggle_available_true_when_eligible_date_in_past(self):
        """is_available=True succeeds when next_eligible_date has passed."""
        token = _next_token()
        _create_profile(token)
        user_id = _get_user_id(token)
        _set_next_eligible(user_id, date.today() - timedelta(days=1))

        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": True},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["is_available"] is True

    def test_toggle_available_false_always_succeeds(self):
        """Setting is_available=False is always allowed, regardless of date."""
        token = _next_token()
        _create_profile(token)
        user_id = _get_user_id(token)
        _set_next_eligible(user_id, date.today() + timedelta(days=30))

        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": False},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["is_available"] is False

    def test_toggle_available_true_when_eligible_date_is_today(self):
        """next_eligible_date == today is NOT in the future, so it should succeed."""
        token = _next_token()
        _create_profile(token)
        user_id = _get_user_id(token)
        _set_next_eligible(user_id, date.today())

        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": True},
            headers=_auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["is_available"] is True


# ---------------------------------------------------------------------------
# 4. Toggle availability fails with 400 when not yet eligible
# ---------------------------------------------------------------------------

class TestAvailabilityToggleNotEligible:
    def test_toggle_available_true_fails_when_future_eligible_date(self):
        """is_available=True must return 400 when next_eligible_date is future."""
        token = _next_token()
        _create_profile(token)
        user_id = _get_user_id(token)
        future = date.today() + timedelta(days=56)
        _set_next_eligible(user_id, future)

        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": True},
            headers=_auth_headers(token),
        )
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert detail["code"] == "NOT_YET_ELIGIBLE"
        assert future.isoformat() in detail["message"]

    def test_toggle_availability_without_profile_returns_404(self):
        """Patching availability without a profile first returns 404."""
        token = _next_token()
        r = client.patch(
            "/api/v1/donors/availability",
            json={"is_available": True},
            headers=_auth_headers(token),
        )
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# 5. Unauthenticated requests return 401
# ---------------------------------------------------------------------------

class TestUnauthenticated:
    def test_post_profile_without_token_returns_401(self):
        r = client.post(
            "/api/v1/donors/profile",
            data={"blood_type": "O+", "latitude": "0.0", "longitude": "0.0"},
        )
        assert r.status_code == 401

    def test_patch_availability_without_token_returns_401(self):
        r = client.patch("/api/v1/donors/availability", json={"is_available": True})
        assert r.status_code == 401

    def test_get_profile_without_token_returns_401(self):
        r = client.get("/api/v1/donors/profile")
        assert r.status_code == 401

    def test_get_history_without_token_returns_401(self):
        r = client.get("/api/v1/donors/1/history")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = client.get(
            "/api/v1/donors/profile",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert r.status_code == 401

