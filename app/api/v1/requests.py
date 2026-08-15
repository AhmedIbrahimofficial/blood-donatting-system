"""
Emergency request endpoints.

All endpoints require a valid JWT (get_current_user dependency).

Routes
------
POST   /api/v1/requests          – create a new EmergencyRequest (async matching)
GET    /api/v1/requests/{id}/status – return status + associated matches
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_user
from app.models.emergency_request import EmergencyRequest, RequestStatus
from app.models.user import User
from app.schemas.emergency_request import (
    EmergencyRequestCreate,
    EmergencyRequestAcceptedResponse,
    EmergencyRequestStatusResponse,
    RequestMatchResponse,
)
from app.tasks.matching_tasks import match_and_notify

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


# ---------------------------------------------------------------------------
# POST / — create a new EmergencyRequest
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=EmergencyRequestAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new emergency blood request",
)
@limiter.limit("5/minute")
def create_request(
    request: Request,
    body: EmergencyRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EmergencyRequestAcceptedResponse:
    """
    Create an :class:`EmergencyRequest` with ``status='open'`` and immediately
    return **202 Accepted**.

    Donor matching and notification dispatch are handled asynchronously by the
    ``match_and_notify`` Celery task.  Poll
    ``GET /api/v1/requests/{id}/status`` to check progress.
    """
    request = EmergencyRequest(
        requester_id=current_user.id,
        blood_type_needed=body.blood_type_needed,
        units_needed=body.units_needed,
        hospital_name=body.hospital_name,
        latitude=body.latitude,
        longitude=body.longitude,
        urgency_level=body.urgency_level,
        status=RequestStatus.open,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Dispatch async task — returns immediately
    match_and_notify.delay(request.id)

    return EmergencyRequestAcceptedResponse(
        id=request.id,
        status=request.status,
        message="Request accepted. Donor matching is in progress.",
    )


# ---------------------------------------------------------------------------
# GET /{id}/status — return request status + matches
# ---------------------------------------------------------------------------


@router.get(
    "/{request_id}/status",
    response_model=EmergencyRequestStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the status of an emergency request",
)
def get_request_status(
    request_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EmergencyRequestStatusResponse:
    """
    Return the current :attr:`~EmergencyRequest.status` and all associated
    :class:`RequestMatch` records for *request_id*.

    Returns **404** if the request does not exist.

    .. note::
        ``matches`` will be empty until notification dispatch is implemented.
    """
    request: EmergencyRequest | None = db.get(EmergencyRequest, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REQUEST_NOT_FOUND",
                "message": f"No emergency request with id={request_id}.",
            },
        )

    matches = [RequestMatchResponse.model_validate(m) for m in request.matches]

    return EmergencyRequestStatusResponse(
        id=request.id,
        status=request.status,
        blood_type_needed=request.blood_type_needed,
        urgency_level=request.urgency_level,
        created_at=request.created_at,
        matches=matches,
    )
