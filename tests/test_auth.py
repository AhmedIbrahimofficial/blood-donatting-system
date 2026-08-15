"""
Tests for /api/v1/auth/google endpoint.

Strategy:
- Firebase token verification is mocked so no real Google account is needed.
- DB uses shared SQLite in-memory engine from conftest.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from tests.conftest import TestingSessionLocal

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fake Firebase claims returned by verify_google_token mock
# ---------------------------------------------------------------------------

FAKE_CLAIMS = {
    "uid": "google_uid_abc123",
    "email": "testuser@gmail.com",
    "name": "Test User",
}


def _google_login(uid: str = "google_uid_abc123", email: str = "testuser@gmail.com") -> dict:
    """Call POST /api/v1/auth/google with mocked Firebase verification."""
    claims = {"uid": uid, "email": email, "name": "Test User"}
    with patch("app.api.v1.auth.verify_google_token", return_value=claims):
        resp = client.post("/api/v1/auth/google", json={"id_token": "fake_token"})
    return resp


# ---------------------------------------------------------------------------
# POST /api/v1/auth/google
# ---------------------------------------------------------------------------


class TestGoogleLogin:
    def test_returns_access_token(self):
        resp = _google_login()
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # JWT has exactly 3 dot-separated segments
        assert data["access_token"].count(".") == 2

    def test_creates_user_in_db_on_first_login(self):
        from app.models.user import User

        _google_login(uid="new_user_uid", email="new@gmail.com")

        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.phone == "google:new_user_uid").first()
            assert user is not None
            assert user.name == "Test User"
            assert user.phone_verified_at is not None
        finally:
            db.close()

    def test_second_login_reuses_existing_user(self):
        """Logging in twice should not create a duplicate user row."""
        from app.models.user import User

        _google_login(uid="returning_uid")
        _google_login(uid="returning_uid")

        db = TestingSessionLocal()
        try:
            count = (
                db.query(User)
                .filter(User.phone == "google:returning_uid")
                .count()
            )
            assert count == 1
        finally:
            db.close()

    def test_invalid_firebase_token_returns_401(self):
        import firebase_admin.auth as fb_auth

        with patch(
            "app.api.v1.auth.verify_google_token",
            side_effect=fb_auth.InvalidIdTokenError("bad token"),
        ):
            resp = client.post("/api/v1/auth/google", json={"id_token": "bad"})

        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "INVALID_GOOGLE_TOKEN"

    def test_missing_id_token_returns_422(self):
        resp = client.post("/api/v1/auth/google", json={})
        assert resp.status_code == 422

    def test_jwt_is_usable_for_authenticated_endpoints(self):
        """Token from /google should grant access to protected endpoints."""
        resp = _google_login(uid="donor_user_uid", email="donor@gmail.com")
        token = resp.json()["access_token"]

        profile_resp = client.get(
            "/api/v1/donors/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 = no profile yet (correct — user exists but no donor profile)
        # 401 = token rejected (wrong)
        assert profile_resp.status_code == 404

    def test_no_token_returns_401_on_protected_endpoint(self):
        resp = client.get("/api/v1/donors/profile")
        assert resp.status_code == 401

    def test_different_google_uids_create_separate_users(self):
        from app.models.user import User

        _google_login(uid="uid_alpha", email="alpha@gmail.com")
        _google_login(uid="uid_beta", email="beta@gmail.com")

        db = TestingSessionLocal()
        try:
            alpha = db.query(User).filter(User.phone == "google:uid_alpha").first()
            beta = db.query(User).filter(User.phone == "google:uid_beta").first()
            assert alpha is not None
            assert beta is not None
            assert alpha.id != beta.id
        finally:
            db.close()
