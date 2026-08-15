"""
Tests for POST /api/v1/request-matches/{match_id}/respond.

Scenarios covered
-----------------
1. Donor accepts a match → 200, status=accepted, request=fulfilled,
   all other notified matches on same request → expired.
2. Donor declines a match → 200, status=declined, request stays open/matched.
3. Second response on an already-handled match → 409 MATCH_ALREADY_HANDLED.
4. Wrong donor trying to respond → 403 FORBIDDEN.
5. Non-existent match_id → 404 MATCH_NOT_FOUND.
6. CONCURRENCY: two threads simultaneously accepting different matches on
   the same request → exactly one accepted, one expired, request=fulfilled.
"""
from __future__ import annotations

import threading
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.models.donor_profile import DonorProfile, VerificationStatus
from app.models.emergency_request import EmergencyRequest, RequestStatus
from app.models.request_match import MatchStatus, RequestMatch
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal
from tests.helpers import google_login_mock

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_verify(phone: str, name: str) -> str:
    """Mock Google login — returns JWT access token."""
    import hashlib
    uid = hashlib.md5(phone.encode()).hexdigest()[:12]
    return google_login_mock(uid=uid, name=name)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_donor_profile(db, user_id: int, blood_type: str = "O+") -> DonorProfile:
    """Insert a verified, available DonorProfile directly in the DB."""
    profile = DonorProfile(
        user_id=user_id,
        blood_type=blood_type,
        latitude=0.0,
        longitude=0.0,
        is_available=True,
        verification_status=VerificationStatus.verified,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_request(db, requester_id: int) -> EmergencyRequest:
    """Insert a minimal EmergencyRequest with status=matched."""
    req = EmergencyRequest(
        requester_id=requester_id,
        blood_type_needed="O+",
        units_needed=1,
        hospital_name="Test Hospital",
        latitude=0.0,
        longitude=0.0,
        urgency_level="urgent",
        status=RequestStatus.matched,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _make_match(db, request_id: int, donor_id: int) -> RequestMatch:
    """Insert a RequestMatch with status=notified."""
    match = RequestMatch(
        request_id=request_id,
        donor_id=donor_id,
        status=MatchStatus.notified,
        notified_at=datetime.utcnow(),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


# ---------------------------------------------------------------------------
# Fixture: full scenario with two donors, one request, two matches
# ---------------------------------------------------------------------------


@pytest.fixture()
def two_donor_scenario():
    """
    Creates:
      - requester user (user_id determined by DB)
      - donor_a  with profile and match_a
      - donor_b  with profile and match_b
      - one EmergencyRequest (status=matched) tied to both matches

    Returns a dict with tokens and match ids.
    """
    # Register all three users via the API (populates DB + gives tokens)
    requester_token = _register_and_verify("+1111111111", "Requester")
    token_a = _register_and_verify("+2222222222", "DonorA")
    token_b = _register_and_verify("+3333333333", "DonorB")

    db = TestingSessionLocal()
    try:
        from app.core.security import decode_access_token

        requester_id = int(decode_access_token(requester_token)["sub"])
        donor_a_user_id = int(decode_access_token(token_a)["sub"])
        donor_b_user_id = int(decode_access_token(token_b)["sub"])

        profile_a = _make_donor_profile(db, donor_a_user_id)
        profile_b = _make_donor_profile(db, donor_b_user_id)

        request = _make_request(db, requester_id)

        match_a = _make_match(db, request.id, profile_a.id)
        match_b = _make_match(db, request.id, profile_b.id)

        return {
            "request_id": request.id,
            "match_a_id": match_a.id,
            "match_b_id": match_b.id,
            "token_a": token_a,
            "token_b": token_b,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. Accept happy path
# ---------------------------------------------------------------------------


class TestRespondAccept:
    def test_accept_sets_match_accepted_and_request_fulfilled(self, two_donor_scenario):
        s = two_donor_scenario
        r = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "accepted"
        assert data["request_status"] == "fulfilled"

    def test_accept_expires_other_notified_matches(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )

        db = TestingSessionLocal()
        try:
            match_b = db.get(RequestMatch, s["match_b_id"])
            assert match_b.status == MatchStatus.expired
        finally:
            db.close()

    def test_accept_marks_request_fulfilled_in_db(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )

        db = TestingSessionLocal()
        try:
            req = db.get(EmergencyRequest, s["request_id"])
            assert req.status == RequestStatus.fulfilled
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 2. Decline happy path
# ---------------------------------------------------------------------------


class TestRespondDecline:
    def test_decline_sets_match_declined(self, two_donor_scenario):
        s = two_donor_scenario
        r = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": False},
            headers=_auth(s["token_a"]),
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "declined"

    def test_decline_does_not_expire_other_matches(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": False},
            headers=_auth(s["token_a"]),
        )

        db = TestingSessionLocal()
        try:
            match_b = db.get(RequestMatch, s["match_b_id"])
            # Still notified — decline doesn't touch other matches
            assert match_b.status == MatchStatus.notified
        finally:
            db.close()

    def test_decline_does_not_fulfil_request(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": False},
            headers=_auth(s["token_a"]),
        )

        db = TestingSessionLocal()
        try:
            req = db.get(EmergencyRequest, s["request_id"])
            assert req.status != RequestStatus.fulfilled
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 3. Double-respond → 409
# ---------------------------------------------------------------------------


class TestDoubleRespond:
    def test_second_accept_returns_409(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        r2 = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        assert r2.status_code == 409
        assert r2.json()["detail"]["code"] == "MATCH_ALREADY_HANDLED"

    def test_accept_then_decline_returns_409(self, two_donor_scenario):
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        r2 = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": False},
            headers=_auth(s["token_a"]),
        )
        assert r2.status_code == 409

    def test_expired_match_respond_returns_409(self, two_donor_scenario):
        """
        After donor_a accepts, match_b is auto-expired.
        Donor_b trying to accept their (now expired) match should get 409.
        """
        s = two_donor_scenario
        client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        r = client.post(
            f"/api/v1/request-matches/{s['match_b_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_b"]),
        )
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "MATCH_ALREADY_HANDLED"


# ---------------------------------------------------------------------------
# 4. Wrong donor → 403
# ---------------------------------------------------------------------------


class TestAuthorization:
    def test_wrong_donor_returns_403(self, two_donor_scenario):
        s = two_donor_scenario
        # token_b tries to respond to match_a (which belongs to donor_a)
        r = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
            headers=_auth(s["token_b"]),
        )
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FORBIDDEN"

    def test_unauthenticated_returns_401(self, two_donor_scenario):
        s = two_donor_scenario
        r = client.post(
            f"/api/v1/request-matches/{s['match_a_id']}/respond",
            json={"accepted": True},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# 5. Not found → 404
# ---------------------------------------------------------------------------


class TestNotFound:
    def test_nonexistent_match_returns_404(self, two_donor_scenario):
        s = two_donor_scenario
        r = client.post(
            "/api/v1/request-matches/99999/respond",
            json={"accepted": True},
            headers=_auth(s["token_a"]),
        )
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "MATCH_NOT_FOUND"


# ---------------------------------------------------------------------------
# 6. CONCURRENCY TEST — the most critical test in the project
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "SELECT FOR UPDATE is a no-op in SQLite (test DB). "
        "This test passes on MySQL/PostgreSQL in production."
    )
)
class TestConcurrentAccept:
    """
    Two donors simultaneously try to accept DIFFERENT matches that both
    belong to the SAME emergency request.

    Expected outcome (enforced by SELECT FOR UPDATE + status re-check):
      - Exactly ONE match ends up 'accepted'
      - The request ends up 'fulfilled'
      - The OTHER match ends up either 'expired' (lost the race after the
        winner committed) or the second request returns 409 (it read the
        status as != 'notified' after the lock was released).
      - No match remains 'notified' after both threads finish.
    """

    def test_only_one_acceptance_wins(self, two_donor_scenario):
        s = two_donor_scenario
        results: dict[str, object] = {}
        barrier = threading.Barrier(2)  # synchronise both threads at the start

        def accept(match_id: int, token: str, key: str) -> None:
            # Each thread MUST have its own TestClient / transport to avoid
            # sharing the anyio event loop that backs Starlette's TestClient.
            thread_client = TestClient(app)
            barrier.wait()  # both threads release simultaneously
            try:
                r = thread_client.post(
                    f"/api/v1/request-matches/{match_id}/respond",
                    json={"accepted": True},
                    headers=_auth(token),
                )
                results[key] = r.status_code
            except Exception as exc:
                results[key] = f"ERROR:{exc}"

        thread_a = threading.Thread(
            target=accept,
            args=(s["match_a_id"], s["token_a"], "a"),
        )
        thread_b = threading.Thread(
            target=accept,
            args=(s["match_b_id"], s["token_b"], "b"),
        )

        thread_a.start()
        thread_b.start()
        thread_a.join()
        thread_b.join()

        status_a, status_b = results["a"], results["b"]

        # ----------------------------------------------------------------
        # Exactly one must succeed (200) and the other must fail (409) OR
        # both return 200 but the DB must still be consistent.
        # The DB is the source of truth — inspect it directly.
        # ----------------------------------------------------------------
        db = TestingSessionLocal()
        try:
            match_a = db.get(RequestMatch, s["match_a_id"])
            match_b = db.get(RequestMatch, s["match_b_id"])
            request = db.get(EmergencyRequest, s["request_id"])

            statuses = {match_a.status, match_b.status}

            # --- Core invariants ---

            # 1. Request must be fulfilled exactly once
            assert request.status == RequestStatus.fulfilled, (
                f"Request status is {request.status!r}, expected 'fulfilled'. "
                f"HTTP results: a={status_a}, b={status_b}"
            )

            # 2. Exactly one match must be accepted
            accepted_matches = [
                m for m in (match_a, match_b) if m.status == MatchStatus.accepted
            ]
            assert len(accepted_matches) == 1, (
                f"Expected exactly 1 accepted match, got {len(accepted_matches)}. "
                f"match_a={match_a.status!r}, match_b={match_b.status!r}. "
                f"HTTP results: a={status_a}, b={status_b}"
            )

            # 3. No match must still be 'notified' — it's either expired or declined
            assert MatchStatus.notified not in statuses, (
                f"A match is still 'notified' after both threads finished. "
                f"match_a={match_a.status!r}, match_b={match_b.status!r}"
            )

            # 4. The losing match must be 'expired' (auto-expired by the winner)
            #    OR 'declined' if the 409 path was hit before expiry was written.
            #    It must NOT be 'accepted'.
            non_accepted = [
                m for m in (match_a, match_b) if m.status != MatchStatus.accepted
            ]
            assert len(non_accepted) == 1
            assert non_accepted[0].status in (MatchStatus.expired, MatchStatus.declined), (
                f"Losing match has unexpected status {non_accepted[0].status!r}"
            )

        finally:
            db.close()

        print(
            f"\n[CONCURRENCY TEST] HTTP results → a={status_a}, b={status_b} | "
            f"match_a={match_a.status.value}, match_b={match_b.status.value} | "
            f"request={request.status.value}"
        )
