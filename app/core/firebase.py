"""
Firebase Admin SDK initialisation — called once at startup.

Verifies Google ID tokens issued by Firebase Authentication.
"""
from __future__ import annotations

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings

_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    """Return the initialised Firebase app, creating it on first call."""
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _app = firebase_admin.initialize_app(cred)
    return _app


def verify_google_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.

    Args:
        id_token: The Firebase ID token sent from the frontend.

    Returns:
        Decoded token claims dict containing at least:
            uid   — Firebase user UID
            email — user's Google email
            name  — display name (if available)

    Raises:
        firebase_admin.auth.InvalidIdTokenError  — token is invalid/expired
        firebase_admin.auth.UserNotFoundError    — UID not found
    """
    get_firebase_app()  # ensure initialised
    return firebase_auth.verify_id_token(id_token)
