"""
Authentication endpoints — Google OAuth via Firebase.

Flow
----
1. Frontend signs the user in with Google using Firebase Authentication SDK.
2. Frontend calls  POST /api/v1/auth/google  with the Firebase ID token.
3. Backend verifies the token with Firebase Admin SDK (no Redis needed).
4. Backend upserts a User row (creates on first login, finds on subsequent).
5. Backend returns a signed JWT access token for all further API calls.

No OTP, no Redis, no passwords.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.limiter import limiter

from app.core.database import get_db
from app.core.firebase import verify_google_token
from app.core.security import create_access_token
from app.models.user import User, UserRole

from datetime import datetime, timezone

import firebase_admin.auth as firebase_auth

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GoogleLoginRequest(BaseModel):
    id_token: str  # Firebase ID token from frontend


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfoResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /google — verify Firebase token, upsert user, return JWT
# ---------------------------------------------------------------------------


@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in / register with Google via Firebase",
)
def google_login(
    request: Request,
    body: GoogleLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Exchange a Firebase ID token for an app-level JWT access token.

    - Verifies the Firebase ID token (checks signature + expiry).
    - Creates a new User row on first login using the Google email as a
      unique identifier.
    - Returns a JWT that all other authenticated endpoints accept.
    """
    # --- 1. Verify Firebase ID token ---------------------------------------
    try:
        claims = verify_google_token(body.id_token)
    except firebase_auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_GOOGLE_TOKEN", "message": str(exc)},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_VERIFICATION_FAILED", "message": str(exc)},
        )

    google_uid: str = claims["uid"]
    email: str = claims.get("email", "")
    name: str = claims.get("name", email.split("@")[0] if email else "User")

    # --- 2. Upsert user row -------------------------------------------------
    # Use google_uid stored in the phone column as a unique key
    # (phone column is unique; prefix prevents collision with real phone numbers)
    uid_key = f"google:{google_uid}"

    user: User | None = db.query(User).filter(User.phone == uid_key).first()

    if user is None:
        user = User(
            phone=uid_key,
            name=name,
            email=email,
            role=UserRole.donor,
            phone_verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update name and email in case they changed in Google account
        updated = False
        if user.name != name:
            user.name = name
            updated = True
        if email and user.email != email:
            user.email = email
            updated = True
        if updated:
            db.commit()

    # --- 3. Issue JWT -------------------------------------------------------
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, token_type="bearer")


# ---------------------------------------------------------------------------
# GET /me — return current user info
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in user info",
)
def get_me(
    db: Annotated[Session, Depends(get_db)],
) -> UserInfoResponse:
    """
    Returns basic info about the current user.
    Frontend can call this after login to display the user's name/email.
    """
    # This is a placeholder — real auth uses get_current_user dependency
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Use Authorization: Bearer <token> header",
    )
