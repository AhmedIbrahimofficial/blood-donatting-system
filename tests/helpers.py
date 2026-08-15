"""
Shared test helpers — replaces the old OTP-based register/verify flow
with a mocked Google OAuth login.
"""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_uid_counter = 0


def _next_uid() -> str:
    global _uid_counter
    _uid_counter += 1
    return f"test_uid_{_uid_counter:04d}"


def google_login_mock(
    uid: str | None = None,
    name: str = "Test User",
    email: str | None = None,
) -> str:
    """
    Call POST /api/v1/auth/google with a mocked Firebase token verification.
    Returns the JWT access token.
    """
    if uid is None:
        uid = _next_uid()
    if email is None:
        email = f"{uid}@test.com"

    claims = {"uid": uid, "email": email, "name": name}
    with patch("app.api.v1.auth.verify_google_token", return_value=claims):
        resp = client.post("/api/v1/auth/google", json={"id_token": "fake"})

    assert resp.status_code == 200, f"Google login failed: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
