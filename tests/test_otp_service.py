"""
OTP service tests — skipped because auth is now Google OAuth.
OtpService code is retained for potential future SMS fallback.
"""
import pytest

pytestmark = pytest.mark.skip(reason="Auth migrated to Google OAuth — OTP service not in use")
