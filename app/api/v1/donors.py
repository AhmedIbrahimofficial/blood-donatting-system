"""
Donor profile endpoints — production hardened.

Security additions:
- File upload: type validation (JPEG/PNG/PDF only), 5 MB size limit
- Pagination on history endpoint
- Rate limiting via slowapi
- Input sanitization via Pydantic validators (already in schemas)
"""
import os
import uuid
from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_user
from app.models.donation_history import DonationHistory
from app.models.donor_profile import DonorProfile
from app.models.user import User
from app.schemas.donor_profile import (
    AvailabilityUpdate,
    DonationHistoryItem,
    DonorProfileCreate,
    DonorProfileResponse,
)
from app.services.storage_service import upload_file

router = APIRouter(prefix="/api/v1/donors", tags=["donors"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "uploads",
)
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}


# ---------------------------------------------------------------------------
# Storage helper
# ---------------------------------------------------------------------------

def _save_upload(file: UploadFile) -> str:
    """Validate and upload file to R2/S3 or local disk."""
    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_FILE_TYPE", "message": "Only JPEG, PNG and PDF files are allowed."},
        )
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_FILE_EXTENSION", "message": f"File extension '{ext}' is not allowed."},
        )
    content = file.file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "FILE_TOO_LARGE", "message": "File must be 5 MB or smaller."},
        )
    return upload_file(content, file.filename or f"upload{ext}", file.content_type or "application/octet-stream")


# ---------------------------------------------------------------------------
# POST /profile
# ---------------------------------------------------------------------------

@router.post(
    "/profile",
    response_model=DonorProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update the current user's donor profile",
)
@limiter.limit("20/minute")
def upsert_profile(
    request: Request,
    blood_type: Annotated[str, Form()],
    latitude: Annotated[float, Form()],
    longitude: Annotated[float, Form()],
    id_document: Annotated[UploadFile | None, File()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> DonorProfileResponse:
    try:
        payload = DonorProfileCreate(
            blood_type=blood_type, latitude=latitude, longitude=longitude
        )
    except ValidationError as exc:
        errors = [{k: v for k, v in e.items() if k != "ctx"} for e in exc.errors()]
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)

    profile: DonorProfile | None = (
        db.query(DonorProfile).filter(DonorProfile.user_id == current_user.id).first()
    )

    if profile is None:
        profile = DonorProfile(user_id=current_user.id)
        db.add(profile)

    profile.blood_type = payload.blood_type
    profile.latitude = payload.latitude
    profile.longitude = payload.longitude

    if id_document is not None and id_document.filename:
        profile.id_document_path = _save_upload(id_document)

    db.commit()
    db.refresh(profile)
    return DonorProfileResponse.model_validate(profile)


# ---------------------------------------------------------------------------
# PATCH /availability
# ---------------------------------------------------------------------------

@router.patch(
    "/availability",
    response_model=DonorProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle the current user's availability to donate",
)
@limiter.limit("30/minute")
def update_availability(
    request: Request,
    body: AvailabilityUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> DonorProfileResponse:
    profile: DonorProfile | None = (
        db.query(DonorProfile).filter(DonorProfile.user_id == current_user.id).first()
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "No donor profile found. Create one first."},
        )

    if body.is_available and profile.next_eligible_date is not None:
        if profile.next_eligible_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "NOT_YET_ELIGIBLE",
                    "message": (
                        f"You cannot mark yourself available before your eligibility "
                        f"date ({profile.next_eligible_date.isoformat()})."
                    ),
                },
            )

    profile.is_available = body.is_available
    db.commit()
    db.refresh(profile)
    return DonorProfileResponse.model_validate(profile)


# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------

@router.get(
    "/profile",
    response_model=DonorProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current user's donor profile",
)
def get_profile(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> DonorProfileResponse:
    profile: DonorProfile | None = (
        db.query(DonorProfile).filter(DonorProfile.user_id == current_user.id).first()
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "No donor profile found. Create one first."},
        )
    return DonorProfileResponse.model_validate(profile)


# ---------------------------------------------------------------------------
# GET /{user_id}/history — with pagination
# ---------------------------------------------------------------------------

@router.get(
    "/{user_id}/history",
    response_model=List[DonationHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Get donation history for a donor (paginated)",
)
def get_donation_history(
    user_id: int,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> List[DonationHistoryItem]:
    """Return paginated donation history. page=1, page_size=20 by default."""
    profile: DonorProfile | None = (
        db.query(DonorProfile).filter(DonorProfile.user_id == user_id).first()
    )
    if profile is None:
        return []

    offset = (page - 1) * page_size
    records: List[DonationHistory] = (
        db.query(DonationHistory)
        .filter(DonationHistory.donor_id == profile.id)
        .order_by(DonationHistory.date.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [DonationHistoryItem.model_validate(r) for r in records]
