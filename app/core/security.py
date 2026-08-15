from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# ---------------------------------------------------------------------------
# OAuth2 scheme — points to the login endpoint that will issue tokens
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Encode a JWT access token.

    Args:
        data: Claims to embed (must include a ``"sub"`` key with the user id).
        expires_delta: Custom TTL. Falls back to ``ACCESS_TOKEN_EXPIRE_MINUTES``
                       from settings when not provided.

    Returns:
        Signed JWT string.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises:
        JWTError: If the token is invalid, malformed, or expired.

    Returns:
        The decoded claims dict.
    """
    # jose raises JWTError (or a subclass) for any validation failure —
    # expired signature, bad signature, malformed token, etc.
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    FastAPI dependency that resolves the currently authenticated user.

    Decodes the Bearer token, extracts the ``sub`` claim (user id), and
    fetches the matching ``User`` row from the database.

    Raises:
        HTTPException 401: Token is missing, invalid, expired, or the user
                           no longer exists in the database.
    """
    # Import here to avoid a circular import at module load time
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    return user
