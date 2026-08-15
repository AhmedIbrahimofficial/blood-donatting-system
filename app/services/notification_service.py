"""
Notification service — sends email alerts via SendGrid.

send_donor_alert_email : alert a matched donor about a blood request
send_request_confirmation_email : confirm receipt to the requester
"""
from __future__ import annotations

import logging

from app.models.donor_profile import DonorProfile
from app.models.emergency_request import EmergencyRequest
from app.models.user import User
from app.services.email_service import (
    send_donor_alert,
    send_request_confirmation,
    send_match_accepted,
)

logger = logging.getLogger(__name__)


def notify_donor(donor_profile: DonorProfile, request: EmergencyRequest, db) -> None:
    """
    Send an email alert to a matched donor.
    Looks up the User row to get the donor's email via Google UID.
    """
    user: User | None = db.get(User, donor_profile.user_id)
    if user is None:
        logger.warning("notify_donor: no user for donor_profile %s", donor_profile.id)
        return

    # Google users have phone = "google:uid" — extract email from DB
    # For now we use a placeholder — in production store email on User model
    donor_email = _get_user_email(user)
    if not donor_email:
        logger.info("notify_donor: no email for user %s — skip", user.id)
        return

    send_donor_alert(
        donor_email=donor_email,
        donor_name=user.name,
        blood_type=request.blood_type_needed,
        hospital_name=request.hospital_name,
        urgency_level=request.urgency_level.value,
        request_id=request.id,
    )


def notify_requester(request: EmergencyRequest, candidates_found: int, db) -> None:
    """Send a confirmation email to the requester."""
    user: User | None = db.get(User, request.requester_id)
    if user is None:
        return

    requester_email = _get_user_email(user)
    if not requester_email:
        return

    send_request_confirmation(
        requester_email=requester_email,
        requester_name=user.name,
        blood_type=request.blood_type_needed,
        hospital_name=request.hospital_name,
        request_id=request.id,
        candidates_found=candidates_found,
    )


def notify_match_accepted(match, db) -> None:
    """Notify requester that a donor accepted."""
    from app.models.request_match import RequestMatch
    from app.models.emergency_request import EmergencyRequest

    request: EmergencyRequest | None = db.get(EmergencyRequest, match.request_id)
    if not request:
        return

    requester: User | None = db.get(User, request.requester_id)
    donor_profile: DonorProfile | None = db.get(DonorProfile, match.donor_id)
    if not requester or not donor_profile:
        return

    donor_user: User | None = db.get(User, donor_profile.user_id)
    requester_email = _get_user_email(requester)
    if not requester_email or not donor_user:
        return

    send_match_accepted(
        requester_email=requester_email,
        requester_name=requester.name,
        donor_name=donor_user.name,
        blood_type=request.blood_type_needed,
        hospital_name=request.hospital_name,
    )


def _get_user_email(user: User) -> str | None:
    """
    Extract email from User record.
    Google users: phone = "google:uid" — we need to store email separately.
    For now returns None if no email column exists.
    """
    # Check if User model has email field
    if hasattr(user, "email") and user.email:
        return user.email
    return None
