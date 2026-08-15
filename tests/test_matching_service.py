"""
Unit tests for app/services/matching_service.py.

Covers:
- get_compatible_donor_types: direction correctness + known cases
- find_candidate_donors: spatial filtering, eligibility filters, distance ordering
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.donor_profile import DonorProfile, VerificationStatus
from app.services.matching_service import find_candidate_donors, get_compatible_donor_types
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_donor(
    db,
    *,
    blood_type: str,
    lat: float,
    lng: float,
    is_available: bool = True,
    verification_status: VerificationStatus = VerificationStatus.verified,
    next_eligible_date: date | None = None,
    user_id: int,
) -> DonorProfile:
    """Insert a minimal DonorProfile row and return the persisted object."""
    donor = DonorProfile(
        user_id=user_id,
        blood_type=blood_type,
        latitude=lat,
        longitude=lng,
        is_available=is_available,
        verification_status=verification_status,
        next_eligible_date=next_eligible_date,
    )
    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor


# ---------------------------------------------------------------------------
# get_compatible_donor_types — compatibility direction tests
# ---------------------------------------------------------------------------


class TestGetCompatibleDonorTypes:
    """
    The key question: "which donor types can give blood to a patient who
    needs *blood_type_needed*?"

    O- is the UNIVERSAL DONOR, meaning O- donors can donate to anyone, but
    that does NOT mean "if you need O- blood, all types are compatible".
    A patient who NEEDS O- can only receive O- blood (Rh-negative patients
    cannot receive Rh-positive blood).
    """

    # --- O- needed: only O- donors qualify -----------------------------------

    def test_O_neg_needed_only_O_neg_compatible(self):
        compatible = get_compatible_donor_types("O-")
        assert compatible == ["O-"]

    def test_O_neg_needed_does_NOT_include_A_pos(self):
        assert "A+" not in get_compatible_donor_types("O-")

    def test_O_neg_needed_does_NOT_include_AB_pos(self):
        # AB+ is universal RECIPIENT, not a donor for O- patients
        assert "AB+" not in get_compatible_donor_types("O-")

    # --- AB+ needed: all types compatible (universal recipient) --------------

    def test_AB_pos_needed_all_eight_types_compatible(self):
        compatible = get_compatible_donor_types("AB+")
        all_types = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        assert set(compatible) == all_types

    def test_AB_pos_needed_includes_O_neg(self):
        assert "O-" in get_compatible_donor_types("AB+")

    # --- A+ needed -----------------------------------------------------------

    def test_A_pos_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("A+"))
        assert compatible == {"A+", "A-", "O+", "O-"}

    def test_A_pos_needed_does_NOT_include_B_pos(self):
        assert "B+" not in get_compatible_donor_types("A+")

    def test_A_pos_needed_does_NOT_include_AB_pos(self):
        assert "AB+" not in get_compatible_donor_types("A+")

    # --- A- needed -----------------------------------------------------------

    def test_A_neg_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("A-"))
        assert compatible == {"A-", "O-"}

    def test_A_neg_needed_does_NOT_include_A_pos(self):
        # Rh-negative patients cannot receive Rh-positive blood
        assert "A+" not in get_compatible_donor_types("A-")

    # --- B+ needed -----------------------------------------------------------

    def test_B_pos_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("B+"))
        assert compatible == {"B+", "B-", "O+", "O-"}

    # --- B- needed -----------------------------------------------------------

    def test_B_neg_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("B-"))
        assert compatible == {"B-", "O-"}

    # --- AB- needed ----------------------------------------------------------

    def test_AB_neg_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("AB-"))
        assert compatible == {"A-", "B-", "AB-", "O-"}

    def test_AB_neg_needed_does_NOT_include_AB_pos(self):
        assert "AB+" not in get_compatible_donor_types("AB-")

    # --- O+ needed -----------------------------------------------------------

    def test_O_pos_needed_compatible_types(self):
        compatible = set(get_compatible_donor_types("O+"))
        assert compatible == {"O+", "O-"}

    def test_O_pos_needed_does_NOT_include_A_pos(self):
        assert "A+" not in get_compatible_donor_types("O+")

    # --- direction: O- is universal DONOR, not universal RECIPIENT ----------

    def test_O_neg_donor_appears_in_every_recipients_list(self):
        """O- should appear as compatible for every recipient blood type."""
        all_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bt in all_types:
            assert "O-" in get_compatible_donor_types(bt), (
                f"O- donor should be compatible with recipient {bt}"
            )

    def test_AB_pos_donor_only_compatible_with_AB_pos_recipient(self):
        """AB+ donors can only give to AB+ recipients."""
        all_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bt in all_types:
            compatible = get_compatible_donor_types(bt)
            if bt == "AB+":
                assert "AB+" in compatible
            else:
                assert "AB+" not in compatible, (
                    f"AB+ donor should NOT be compatible with recipient {bt}"
                )

    # --- invalid input -------------------------------------------------------

    def test_invalid_blood_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown blood type"):
            get_compatible_donor_types("Z+")

    def test_lowercase_input_raises_value_error(self):
        # Input is not normalised inside the function — callers must pass
        # normalised strings (same contract as DonorProfileCreate validator)
        with pytest.raises(ValueError):
            get_compatible_donor_types("o-")


# ---------------------------------------------------------------------------
# find_candidate_donors — spatial + eligibility filtering
# ---------------------------------------------------------------------------

# Nairobi area coordinates used as the origin for all spatial tests.
# ~1 km north:  lat -1.2601, lng 36.8073
# ~3 km north:  lat -1.2331, lng 36.8073
# ~8 km north:  lat -1.1873, lng 36.8073  (outside default 5 km radius)
# Same spot:    lat -1.2864, lng 36.8073

_ORIGIN_LAT = -1.2864
_ORIGIN_LNG = 36.8073

_1KM_NORTH = (-1.2774, 36.8073)   # ≈ 1 km
_3KM_NORTH = (-1.2594, 36.8073)   # ≈ 3 km
_8KM_NORTH = (-1.2144, 36.8073)   # ≈ 8 km  — outside default 5 km radius


class TestFindCandidateDonors:
    """All tests share the autouse reset_state fixture from conftest."""

    # ------------------------------------------------------------------
    # Basic spatial filtering
    # ------------------------------------------------------------------

    def test_returns_donors_within_radius(self):
        db = TestingSessionLocal()
        try:
            _make_donor(db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=1)
            _make_donor(db, blood_type="O+", lat=_3KM_NORTH[0], lng=_3KM_NORTH[1], user_id=2)
            _make_donor(db, blood_type="O+", lat=_8KM_NORTH[0], lng=_8KM_NORTH[1], user_id=3)

            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert len(result) == 2
        # Both returned donors should be the 1 km and 3 km ones (user_id 1 & 2)
        user_ids = {d.user_id for d in result}
        assert user_ids == {1, 2}

    def test_donor_outside_radius_excluded(self):
        db = TestingSessionLocal()
        try:
            _make_donor(db, blood_type="O+", lat=_8KM_NORTH[0], lng=_8KM_NORTH[1], user_id=1)
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert result == []

    # ------------------------------------------------------------------
    # Distance ordering
    # ------------------------------------------------------------------

    def test_results_ordered_nearest_first(self):
        db = TestingSessionLocal()
        try:
            # Insert in reverse distance order to confirm sorting is applied
            _make_donor(db, blood_type="O+", lat=_3KM_NORTH[0], lng=_3KM_NORTH[1], user_id=10)
            _make_donor(db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=11)

            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert len(result) == 2
        # Nearest (user_id=11, 1 km) should come first
        assert result[0].user_id == 11
        assert result[1].user_id == 10

    # ------------------------------------------------------------------
    # Blood type compatibility filtering
    # ------------------------------------------------------------------

    def test_incompatible_blood_type_excluded(self):
        """A B+ donor is NOT compatible with an O- patient."""
        db = TestingSessionLocal()
        try:
            _make_donor(db, blood_type="B+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=1)
            result = find_candidate_donors(db, "O-", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert result == []

    def test_O_neg_donor_compatible_with_any_recipient(self):
        """O- donor should be found regardless of recipient blood type."""
        db = TestingSessionLocal()
        try:
            _make_donor(db, blood_type="O-", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=1)
            for bt in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]:
                result = find_candidate_donors(db, bt, _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
                assert len(result) == 1, f"O- donor should match recipient {bt}"
        finally:
            db.close()

    def test_multiple_compatible_types_all_returned(self):
        """An A+ patient should match A+, A-, O+, and O- donors."""
        db = TestingSessionLocal()
        try:
            for uid, bt in enumerate(["A+", "A-", "O+", "O-"], start=1):
                _make_donor(db, blood_type=bt, lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=uid)
            # Incompatible — should be excluded
            _make_donor(db, blood_type="B+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=99)

            result = find_candidate_donors(db, "A+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        returned_types = {d.blood_type for d in result}
        assert returned_types == {"A+", "A-", "O+", "O-"}

    # ------------------------------------------------------------------
    # Availability filter
    # ------------------------------------------------------------------

    def test_unavailable_donor_excluded(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                is_available=False, user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert result == []

    # ------------------------------------------------------------------
    # Verification status filter
    # ------------------------------------------------------------------

    def test_unverified_donor_excluded(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                verification_status=VerificationStatus.pending, user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert result == []

    def test_rejected_donor_excluded(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                verification_status=VerificationStatus.rejected, user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert result == []

    # ------------------------------------------------------------------
    # next_eligible_date filter
    # ------------------------------------------------------------------

    def test_donor_with_future_eligible_date_excluded(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                next_eligible_date=date.today() + timedelta(days=30), user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert result == []

    def test_donor_eligible_today_included(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                next_eligible_date=date.today(), user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert len(result) == 1

    def test_donor_eligible_yesterday_included(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                next_eligible_date=date.today() - timedelta(days=1), user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert len(result) == 1

    def test_donor_with_null_eligible_date_included(self):
        db = TestingSessionLocal()
        try:
            _make_donor(
                db, blood_type="O+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                next_eligible_date=None, user_id=1,
            )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert len(result) == 1

    # ------------------------------------------------------------------
    # Combined scenario: mixed eligible/ineligible donors, verify order
    # ------------------------------------------------------------------

    def test_combined_filters_and_ordering(self):
        """
        Seed 5 donors; only 2 should pass all filters, and they must be
        returned nearest-first.
        """
        db = TestingSessionLocal()
        try:
            # Should be returned — nearest
            _make_donor(db, blood_type="A+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1], user_id=1)
            # Should be returned — farther
            _make_donor(db, blood_type="O-", lat=_3KM_NORTH[0], lng=_3KM_NORTH[1], user_id=2)
            # Excluded: outside radius
            _make_donor(db, blood_type="A+", lat=_8KM_NORTH[0], lng=_8KM_NORTH[1], user_id=3)
            # Excluded: not available
            _make_donor(
                db, blood_type="A+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                is_available=False, user_id=4,
            )
            # Excluded: future eligible date
            _make_donor(
                db, blood_type="A+", lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                next_eligible_date=date.today() + timedelta(days=10), user_id=5,
            )

            result = find_candidate_donors(db, "A+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert len(result) == 2
        assert result[0].user_id == 1   # 1 km — nearest
        assert result[1].user_id == 2   # 3 km — farther

    # ------------------------------------------------------------------
    # Limit: no more than 10 results
    # ------------------------------------------------------------------

    def test_results_capped_at_10(self):
        db = TestingSessionLocal()
        try:
            for uid in range(1, 16):  # 15 eligible donors
                _make_donor(
                    db, blood_type="O+",
                    lat=_1KM_NORTH[0], lng=_1KM_NORTH[1],
                    user_id=uid,
                )
            result = find_candidate_donors(db, "O+", _ORIGIN_LAT, _ORIGIN_LNG, radius_km=5.0)
        finally:
            db.close()

        assert len(result) <= 10

    # ------------------------------------------------------------------
    # Empty result
    # ------------------------------------------------------------------

    def test_no_donors_returns_empty_list(self):
        db = TestingSessionLocal()
        try:
            result = find_candidate_donors(db, "AB+", _ORIGIN_LAT, _ORIGIN_LNG)
        finally:
            db.close()

        assert result == []
