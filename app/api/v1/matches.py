"""
Request-match response endpoint.

Routes
------
POST /api/v1/request-matches/{match_id}/respond
    – donor accepts or declines a blood-donation match notification.

Concurrency safety
------------------
The endpoint acquires a row-level lock (SELECT … FOR UPDATE) inside an
explicit transaction so that two simultaneous acceptances for the same
emergency request cannot both succeed.  Only the first committer wins;
the second sees status != 'notified' and receives HTTP 409.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.emergency_request import EmergencyRequest, RequestStatus
from app.models.request_match import MatchStatus, RequestMatch
from app.models.user import User

router = APIRouter(prefix="/api/v1/request-matches", tags=["matches"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RespondRequest(BaseModel):
    accepted: bool


class RespondResponse(BaseModel):
    match_id: int
    status: MatchStatus
    request_status: RequestStatus

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /{match_id}/respond
# ---------------------------------------------------------------------------


@router.post(
    "/{match_id}/respond",
    response_model=RespondResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept or decline a blood-donation match notification",
)
def respond_to_match(
    match_id: int,
    body: RespondRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RespondResponse:
    """
    Donor accepts or declines a :class:`RequestMatch` notification.

    Safety guarantees
    -----------------
    1. Opens an explicit transaction and acquires a **row-level lock** on the
       ``RequestMatch`` row via ``SELECT … FOR UPDATE``.  Any concurrent call
       for the *same match* blocks until this transaction completes.
    2. Re-checks ``match.status == 'notified'`` *after* acquiring the lock.
       If a concurrent request already handled this match the check fails
       and we return **409 Conflict** immediately.
    3. On acceptance:
       - Sets this match → ``accepted``
       - Sets the parent :class:`EmergencyRequest` → ``fulfilled``
       - Bulk-expires all *other* ``notified`` matches on the same request
         so no other donor can still accept.
    4. On declination: sets this match → ``declined``.

    Authorization
    -------------
    Only the donor who *owns* the match (i.e. ``match.donor.user_id == current_user.id``)
    may call this endpoint.  Returns **403** otherwise.  Returns **404** when
    the match does not exist.
    """
    # --- 1. Acquire row lock ------------------------------------------------
    match: RequestMatch | None = (
        db.query(RequestMatch)
        .filter(RequestMatch.id == match_id)
        .with_for_update()
        .first()
    )

    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MATCH_NOT_FOUND",
                "message": f"No match with id={match_id}.",
            },
        )

    # --- 2. Authorization check --------------------------------------------
    # Eagerly load the donor relationship so we can inspect user_id.
    if match.donor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You are not the donor for this match.",
            },
        )

    # --- 3. Idempotency / conflict guard ------------------------------------
    if match.status != MatchStatus.notified:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MATCH_ALREADY_HANDLED",
                "message": "This request has already been handled.",
            },
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)  # store as naive UTC

    # --- 4. Apply response --------------------------------------------------
    if body.accepted:
        match.status = MatchStatus.accepted
        match.responded_at = now

        # Mark the parent request as fulfilled
        request: EmergencyRequest = db.get(EmergencyRequest, match.request_id)
        request.status = RequestStatus.fulfilled

        # Expire all OTHER still-notified matches for this request
        other_notified = (
            db.query(RequestMatch)
            .filter(
                RequestMatch.request_id == match.request_id,
                RequestMatch.id != match.id,
                RequestMatch.status == MatchStatus.notified,
            )
            .all()
        )
        for other in other_notified:
            other.status = MatchStatus.expired

    else:
        match.status = MatchStatus.declined
        match.responded_at = now

    # --- 5. Commit ----------------------------------------------------------
    db.commit()
    db.refresh(match)

    # Send email notification to requester if donor accepted
    if body.accepted:
        try:
            from app.services.notification_service import notify_match_accepted
            notify_match_accepted(match=match, db=db)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Match accepted email failed: %s", e)

    request_status = db.get(EmergencyRequest, match.request_id).status

    return RespondResponse(
        match_id=match.id,
        status=match.status,
        request_status=request_status,
    )
