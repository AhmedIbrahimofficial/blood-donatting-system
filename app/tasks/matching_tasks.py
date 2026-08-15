"""
Celery tasks for donor matching and email notification dispatch.
Uses Upstash Redis as the broker.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="match_and_notify", bind=True, max_retries=3)
def match_and_notify(self, request_id: int) -> dict:
    """
    Find candidate donors for *request_id* using expanding radius search,
    create RequestMatch records, and send email notifications.

    Radius strategy: start 5 km, expand by 5 km up to 50 km.
    Stop when 3+ candidates found.
    """
    from app.core.database import SessionLocal
    from app.models.emergency_request import EmergencyRequest, RequestStatus
    from app.models.request_match import RequestMatch, MatchStatus
    from app.services.matching_service import find_candidate_donors
    from app.services.notification_service import notify_donor, notify_requester

    db = SessionLocal()
    try:
        request: EmergencyRequest | None = db.get(EmergencyRequest, request_id)
        if request is None:
            logger.error("match_and_notify: request %s not found", request_id)
            return {"error": f"Request {request_id} not found"}

        # ── Expanding-radius search ─────────────────────────────────────
        MIN_RADIUS_KM   = 5.0
        MAX_RADIUS_KM   = 50.0
        STEP_KM         = 5.0
        TARGET          = 3

        candidates = []
        radius_km  = MIN_RADIUS_KM

        while radius_km <= MAX_RADIUS_KM:
            candidates = find_candidate_donors(
                db=db,
                blood_type_needed=request.blood_type_needed,
                lat=request.latitude,
                lng=request.longitude,
                radius_km=radius_km,
            )
            logger.info(
                "match_and_notify: req=%s radius=%.1fkm candidates=%d",
                request_id, radius_km, len(candidates),
            )
            if len(candidates) >= TARGET:
                break
            radius_km += STEP_KM

        # ── Create matches + notify donors ──────────────────────────────
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        matches_created = 0

        for donor in candidates:
            match = RequestMatch(
                request_id=request.id,
                donor_id=donor.id,
                status=MatchStatus.notified,
                notified_at=now,
            )
            db.add(match)
            db.flush()

            # Send email alert to donor
            try:
                notify_donor(donor_profile=donor, request=request, db=db)
            except Exception as e:
                logger.warning("Email to donor %s failed: %s", donor.id, e)

            matches_created += 1

        # ── Update request status ───────────────────────────────────────
        if matches_created > 0:
            request.status = RequestStatus.matched

        db.commit()

        # ── Send confirmation email to requester ────────────────────────
        try:
            notify_requester(request=request, candidates_found=matches_created, db=db)
        except Exception as e:
            logger.warning("Confirmation email failed for request %s: %s", request_id, e)

        logger.info(
            "match_and_notify: req=%s done — %d match(es), radius=%.1fkm",
            request_id, matches_created, radius_km,
        )
        return {
            "request_id": request_id,
            "matches_created": matches_created,
            "final_radius_km": radius_km,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("match_and_notify: error for request %s", request_id)
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
